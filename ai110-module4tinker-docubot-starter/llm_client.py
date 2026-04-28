import os
import logging
from google import genai

logger = logging.getLogger(__name__)

GEMINI_MODEL_NAME = "gemini-2.5-flash"


class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Missing GEMINI_API_KEY. Set it in your .env file to enable LLM features."
            )
        self.client = genai.Client(api_key=api_key)
        self._verify_model()

    def _verify_model(self):
        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL_NAME,
                contents="Say OK and nothing else."
            )
            logger.info("Model check passed: %s", (response.text or "").strip())
        except Exception as e:
            raise RuntimeError(
                f"Model '{GEMINI_MODEL_NAME}' is unavailable. "
                f"Update GEMINI_MODEL_NAME in llm_client.py.\nError: {e}"
            )

    def _generate(self, prompt):
        response = self.client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=prompt
        )
        return (response.text or "").strip()

    def expand_query(self, query):
        """Rewrites a plain-language query into technical keywords for better retrieval."""
        prompt = (
            f'A beginner developer asked: "{query}"\n\n'
            "Rewrite this as a short list of precise technical keywords a senior developer would use. "
            "Return only the keywords, no explanation, no punctuation, no bullet points."
        )
        try:
            expanded = self._generate(prompt)
            logger.info("Query expanded: '%s' → '%s'", query, expanded)
            return expanded if expanded else query
        except Exception as e:
            logger.warning("Query expansion failed, using original. (%s)", e)
            return query

    def naive_answer_over_full_docs(self, query, all_text):
        prompt = f"You are a software engineering assistant. Answer this question:\n\n{query}"
        try:
            return self._generate(prompt)
        except Exception as e:
            return f"Unable to generate an answer. ({type(e).__name__}: {e})"

    def answer_from_snippets(self, query, snippets):
        if not snippets:
            return "I do not know based on the docs I have."

        context = "\n\n".join(f"File: {fname}\n{text}" for fname, text in snippets)
        prompt = f"""You are a cautious documentation assistant.

Answer the question using only the snippets below. If they don't contain enough information, reply exactly: "I do not know based on the docs I have."
When you answer, mention which files you relied on.

Snippets:
{context}

Question: {query}"""
        try:
            return self._generate(prompt)
        except Exception as e:
            return f"API error — could not generate answer. ({type(e).__name__}: {e})"

    def generate_full_plan(self, project_paragraph, snippets):
        """Generates a complete structured project plan grounded in retrieved docs."""
        docs_block = (
            "\n\n".join(f"[{fname}]\n{text}" for fname, text in snippets)
            if snippets else "No documentation retrieved."
        )

        prompt = f"""You are a senior software engineer mentoring a beginner developer.

Project description:
{project_paragraph}

Using ONLY the documentation below, generate a complete implementation plan broken into 4-6 phases.
For each phase, list 3-5 numbered steps. For each step, explain what to do and why it matters in one beginner-friendly sentence.
If a step isn't covered by the docs, write: "Research needed: [topic]"

Documentation:
{docs_block}

Format (no intro, no summary — just the phases):

## Phase 1: [Name]
1. [What to do] — [Why it matters]
...

## Phase 2: [Name]
..."""
        try:
            result = self._generate(prompt)
            logger.info("Plan generated (%d chars)", len(result))
            return result
        except Exception as e:
            logger.error("Plan generation failed: %s", e, exc_info=True)
            return f"Could not generate plan. ({type(e).__name__}: {e})"
