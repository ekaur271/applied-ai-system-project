"""
Gemini client wrapper used by DocuBot.

Handles:
- Configuring the Gemini client from the GEMINI_API_KEY environment variable
- Naive "generation only" answers over the full docs corpus (Phase 0)
- RAG style answers that use only retrieved snippets (Phase 2)

Experiment with:
- Prompt wording
- Refusal conditions
- How strictly the model is instructed to use only the provided context
"""

import os
import logging
from google import genai

logger = logging.getLogger(__name__)

# Central place to update the model name if needed.
# You can swap this for a different Gemini model in the future.
GEMINI_MODEL_NAME = "gemini-2.5-flash"


class GeminiClient:
    """
    Simple wrapper around the Gemini model.

    Usage:
        client = GeminiClient()
        answer = client.naive_answer_over_full_docs(query, all_text)
        # or
        answer = client.answer_from_snippets(query, snippets)
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Missing GEMINI_API_KEY environment variable. "
                "Set it in your shell or .env file to enable LLM features."
            )

        self.client = genai.Client(api_key=api_key)
        self._verify_model()

    def _verify_model(self):
        """Test the model with a minimal call at startup so we fail fast with a clear message."""
        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents="Say the word OK and nothing else."
            )
            logger.info("Model check passed: %s", (response.text or "").strip())
        except Exception as e:
            raise RuntimeError(
                f"Model '{GEMINI_MODEL_NAME}' is not available on your account.\n"
                f"Error: {e}\n"
                f"Try updating GEMINI_MODEL_NAME in llm_client.py."
            )

    # -----------------------------------------------------------
    # Query expansion: rewrite beginner query using technical terms
    # -----------------------------------------------------------

    def expand_query(self, query):
        """
        Rewrites a plain-language query into technical SWE terminology
        so keyword retrieval can find the right docs even when the user
        doesn't know the exact terms.

        Returns the expanded query string, or the original if the LLM fails.
        """
        prompt = f"""You are a software engineering expert.
A beginner developer wrote this question:
"{query}"

Rewrite it as a short list of precise technical keywords and phrases a senior developer would use.
Return only the keywords, nothing else. No explanation, no punctuation, no bullet points.
Example output: JWT authentication token hashing bcrypt middleware route protection
"""
        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt
            )
            expanded = (response.text or "").strip()
            logger.info("Query expanded: '%s' → '%s'", query, expanded)
            return expanded if expanded else query
        except Exception as e:
            logger.warning("Query expansion failed, using original query. (%s: %s)", type(e).__name__, e)
            return query

    # -----------------------------------------------------------
    # Phase 0: naive generation over full docs
    # -----------------------------------------------------------

    def naive_answer_over_full_docs(self, query, all_text):
        # We ignore all_text and send a generic prompt instead
        prompt = f"""
    You are a documentation assistant. 
    Answer this developer question: {query}
    """
        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt
            )
            return (response.text or "").strip()
        except Exception as e:
            return f"Unable to generate an answer. ({type(e).__name__}: {e})"

    # -----------------------------------------------------------
    # Phase 2: RAG style generation over retrieved snippets
    # -----------------------------------------------------------

    def answer_from_snippets(self, query, snippets):
        """
        Phase 2:
        Generate an answer using only the retrieved snippets.

        snippets: list of (filename, text) tuples selected by DocuBot.retrieve

        The prompt:
        - Shows each snippet with its filename
        - Instructs the model to rely only on these snippets
        - Requires an explicit "I do not know" refusal when needed
        """

        if not snippets:
            return "I do not know based on the docs I have."

        context_blocks = []
        for filename, text in snippets:
            block = f"File: {filename}\n{text}\n"
            context_blocks.append(block)

        context = "\n\n".join(context_blocks)

        prompt = f"""
You are a cautious documentation assistant helping developers understand a codebase.

You will receive:
- A developer question
- A small set of snippets from project files

Your job:
- Answer the question using only the information in the snippets.
- If the snippets do not provide enough evidence, refuse to guess.

Snippets:
{context}

Developer question:
{query}

Rules:
- Use only the information in the snippets. Do not invent new functions,
  endpoints, or configuration values.
- If the snippets are not enough to answer confidently, reply exactly:
  "I do not know based on the docs I have."
- When you do answer, briefly mention which files you relied on.
"""

        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt
            )
            return (response.text or "").strip()
        except Exception as e:
            return f"API error — could not generate answer. ({type(e).__name__}: {e})"

    # -----------------------------------------------------------
    # Planner: generate full project plan in one call
    # -----------------------------------------------------------

    def generate_full_plan(self, project_paragraph, snippets):
        """
        Generates a complete structured project plan in a single LLM call.
        Grounds each phase in the retrieved documentation snippets.
        """
        if snippets:
            docs_block = "\n\n".join(f"[{fname}]\n{text}" for fname, text in snippets)
        else:
            docs_block = "No documentation retrieved."

        prompt = f"""You are a senior software engineer mentoring a beginner developer who wants to build a real project.

Here is their project description:
{project_paragraph}

Using ONLY the documentation below, generate a complete implementation plan broken into 4-6 phases.

For each phase:
- Give it a clear, specific name
- List 3-5 concrete, numbered steps
- For each step, explain what to do AND why it matters in one beginner-friendly sentence
- If a step is not covered by the documentation, write: "Research needed: [topic]" as the step

Documentation:
{docs_block}

Format your response exactly like this — no intro, no summary, just the phases:

## Phase 1: [Phase Name]
1. [What to do] — [Why it matters]
2. [What to do] — [Why it matters]
...

## Phase 2: [Phase Name]
...
"""
        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt
            )
            result = (response.text or "").strip()
            logger.info("Full plan generated successfully (%d chars)", len(result))
            return result
        except Exception as e:
            logger.error("Full plan generation failed: %s", str(e), exc_info=True)
            return f"Could not generate plan. ({type(e).__name__}: {e})"

    # -----------------------------------------------------------
    # Planner: decompose project into phases (kept for reference)
    # -----------------------------------------------------------

    def decompose_into_phases(self, context):
        """
        Takes the assembled project context and returns a list of
        phase names representing the logical stages of the project.
        Returns a list of strings, e.g. ["Project Setup", "Database Design", ...]
        """
        prompt = f"""You are a senior software engineer helping a beginner plan a coding project.

Given the following project context, break the project into 4-6 logical implementation phases.
Return ONLY a numbered list of short phase names. Nothing else. No descriptions, no explanations.

Example output:
1. Project Setup and Environment
2. Database Design
3. Authentication
4. Core API Endpoints
5. Testing and Error Handling
6. Deployment

Project context:
{context}
"""
        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt
            )
            raw = (response.text or "").strip()
            logger.info("Raw phases from LLM: %s", raw)

            # Parse numbered list into a clean list of phase names
            phases = []
            for line in raw.splitlines():
                line = line.strip()
                if line and line[0].isdigit():
                    # Strip leading "1. " or "1) "
                    phase = line.split(".", 1)[-1].split(")", 1)[-1].strip()
                    if phase:
                        phases.append(phase)
            return phases

        except Exception as e:
            logger.error("Phase decomposition failed: %s", str(e), exc_info=True)
            return ["Project Setup", "Core Features", "Testing and Error Handling", "Deployment"]

    # -----------------------------------------------------------
    # Planner: generate steps for a single phase
    # -----------------------------------------------------------

    def generate_phase_steps(self, phase, context, snippets):
        """
        Generates concrete, beginner-friendly implementation steps for a
        single project phase, grounded in the retrieved documentation snippets.
        """
        if snippets:
            context_blocks = "\n\n".join(f"[{fname}]\n{text}" for fname, text in snippets)
        else:
            context_blocks = "No specific documentation retrieved for this phase."

        prompt = f"""You are a senior software engineer mentoring a beginner developer.

Project context:
{context}

You are writing the implementation steps for this phase: {phase}

Use the documentation below to ground your steps in real practices.
If the documentation does not cover something needed for this phase, say "Research needed: [topic]" as a step.

Documentation:
{context_blocks}

Write 3-5 concrete, numbered steps for this phase.
For each step:
- Say exactly what to do
- Explain in one sentence WHY it matters
- Keep language beginner-friendly — avoid jargon without explanation

Return only the steps. No intro, no summary.
"""
        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents=prompt
            )
            return (response.text or "").strip()
        except Exception as e:
            logger.error("Phase step generation failed for '%s': %s", phase, str(e), exc_info=True)
            return f"Could not generate steps for this phase. ({type(e).__name__}: {e})"
