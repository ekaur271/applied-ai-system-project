# AI Integration

## Overview
Integrating AI into an application means connecting your code to an LLM (Large Language Model) API and using it to generate, retrieve, classify, or reason about content. AI integration requires careful prompt design, error handling, and guardrails to produce reliable, trustworthy output.

## When to Use AI
Use AI when the task benefits from natural language understanding or generation:
- Summarizing or explaining content
- Answering questions about documents (RAG)
- Generating structured output from unstructured input
- Classifying or tagging content
- Planning or decomposing a task into steps

Do not use AI when a deterministic function will do — parsing a date, validating an email, sorting a list.

## API Keys and Configuration
Store API keys in environment variables. Never hardcode them.

```python
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY environment variable")
```

## Calling the Gemini API
```python
from google import genai

client = genai.Client(api_key=API_KEY)

def generate(prompt):
    response = client.models.generate_content(
        model="gemma-3-27b-it",
        contents=prompt
    )
    return (response.text or "").strip()
```

## Prompt Design
The quality of AI output depends heavily on prompt quality.

**Be specific about the task:**
```python
# Vague
prompt = f"Answer this: {question}"

# Specific
prompt = f"""
You are a software engineering assistant helping a developer plan a project.

Given the following project goal and context, generate a structured implementation plan.
Use only the information provided. If you cannot answer from the context, say so.

Context:
{context}

Goal: {question}

Format your response as numbered phases with 3-5 steps each.
"""
```

**Key prompt principles:**
- State the role ("You are a...")
- Describe the task precisely
- Provide the context explicitly
- Define the output format
- Add refusal instructions when grounding is important

## Retrieval-Augmented Generation (RAG)
RAG grounds AI output in real documents instead of relying on the model's training data.

```python
def answer_with_rag(query, retriever, llm_client):
    # 1. Retrieve relevant docs
    snippets = retriever.retrieve(query, top_k=3)

    if not snippets:
        return "I could not find relevant documentation to answer this question."

    # 2. Build context from retrieved snippets
    context = "\n\n".join(f"[{fname}]\n{text}" for fname, text in snippets)

    # 3. Generate grounded answer
    prompt = f"""
Answer the question using only the documentation snippets below.
If the snippets do not contain enough information, say "I do not know based on the provided docs."

Documentation:
{context}

Question: {query}
"""
    return llm_client.generate(prompt)
```

## Fallback Behavior
AI APIs can fail — rate limits, network errors, model errors. Always handle gracefully:

```python
def safe_generate(prompt, fallback="I was unable to generate a response. Please try again."):
    try:
        return llm_client.generate(prompt)
    except Exception as e:
        logger.error("LLM generation failed: %s", str(e), exc_info=True)
        return fallback
```

## Guardrails
Prevent the AI from producing harmful or incorrect output:
- Validate that output matches expected format before returning it
- Set explicit refusal instructions in prompts ("if you do not know, say so")
- Check output length and truncate if necessary
- Log all LLM calls and responses for debugging

## Agentic Workflows
An agentic workflow lets the AI plan and execute multi-step tasks:
1. **Plan** — AI breaks a goal into steps
2. **Act** — AI or code executes each step
3. **Observe** — AI checks results
4. **Iterate** — AI adjusts based on what it observed

```python
def plan_project(goal, clarifications, retriever, llm_client):
    # Step 1: Decompose goal into phases
    phases = decompose_goal(goal, clarifications, llm_client)

    # Step 2: For each phase, retrieve relevant docs and generate steps
    plan = []
    for phase in phases:
        snippets = retriever.retrieve(phase, top_k=3)
        steps = generate_phase_steps(phase, snippets, llm_client)
        plan.append({"phase": phase, "steps": steps})

    return plan
```

## Common AI Integration Mistakes
- Hardcoding API keys in source code
- No error handling around API calls
- Prompts that allow hallucination (no grounding or refusal instructions)
- Not logging what was sent to the model and what came back
- Trusting AI output without validation
- No fallback when the API is unavailable
