# DocuBot Project Planner

An agentic AI system that helps developers plan coding projects from scratch using Retrieval-Augmented Generation (RAG). The user describes a project idea, answers a few clarifying questions, and receives a structured, phase-by-phase implementation plan grounded in real software engineering best practices.

---

## Original Project

This system is built on top of **DocuBot** (Module 4 Tinker Activity), a documentation Q&A assistant originally designed to answer developer questions about a codebase. DocuBot's core capability was retrieving relevant snippets from a set of local markdown files and optionally passing them to a Gemini LLM to generate a grounded answer. It supported three modes: naive LLM generation, retrieval only, and full RAG. This project extends that retrieval and generation pipeline into an agentic planning system.

---

## Title and Summary

**DocuBot Project Planner** turns a simple project idea into a concrete, actionable development plan — without hallucinating steps that don't exist. Instead of generating advice from scratch, the planner retrieves relevant best-practice documentation for each phase of the project and uses that retrieved context to ground every step in the plan. This matters because AI-generated plans are often generic or wrong. By anchoring each step to real documentation, the system produces plans that are specific, consistent, and trustworthy.

---

## Architecture Overview

The system follows a four-stage agentic pipeline:

1. **Clarification** — The user submits a project goal. The agent generates 2-3 targeted clarifying questions (stack, scale, key features) and waits for answers before proceeding.
2. **Decomposition** — The Planner Agent breaks the goal and clarifying answers into logical project phases (e.g. Project Structure, Auth, Database, API Design, Deployment).
3. **Retrieval (RAG)** — For each phase, the Retriever queries the knowledge base of best-practice `.md` files and returns the most relevant snippets using keyword-based scoring.
4. **Generation** — The LLM (Gemini) receives the phase name and retrieved snippets and generates a concrete, grounded set of steps. If snippets are insufficient, it flags the gap rather than guessing.

An Evaluator runs separately to measure retrieval hit rate and plan grounding quality.

```
User Goal
  └─→ Clarifier → Clarifying Questions → User Answers
        └─→ Planner Agent → Phases
              └─→ [For each phase] Retriever → Knowledge Base → Snippets
                    └─→ LLM (Gemini) → Grounded Plan Step
                          └─→ Final Structured Plan
                                └─→ Evaluator → Hit Rate + Grounding Score
```

See [assets/system-diagram.png](../assets/system-diagram.png) for the full visual diagram.

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/ekaur271/applied-ai-system-project.git
cd applied-ai-system-project/ai110-module4tinker-docubot-starter
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

```bash
cp .env.example .env
```

Open `.env` and add your Gemini API key:

```
GEMINI_API_KEY=your_api_key_here
```

You can get a free key at [aistudio.google.com](https://aistudio.google.com).

### 5. Run the planner

```bash
python main.py
```

### 6. Run the evaluator (optional)

```bash
python evaluation.py
```

**Requirements:** Python 3.9+, a Gemini API key for LLM modes. No database or server setup required.

---

## Sample Interactions

> **Note:** Fill in these examples after running the system. Include the exact input you typed and paste the actual output. Aim for 2-3 varied examples.

**Example 1**

```
Input:  "I want to build a web app where users can log in and manage their projects"
Clarifying questions: [paste questions the agent asked]
User answers: [paste your answers]

Plan output:
[paste the full plan here]
```

**Example 2**

```
Input:  "I want to build a REST API for a to-do list app"
Clarifying questions: [paste questions]
User answers: [paste your answers]

Plan output:
[paste the full plan here]
```

**Example 3**

```
Input:  "I want to build a simple CLI tool that tracks my daily expenses"
Clarifying questions: [paste questions]
User answers: [paste your answers]

Plan output:
[paste the full plan here]
```

---

## Design Decisions

**Why RAG instead of just asking the LLM?**
A plain LLM prompt produces generic advice that varies between runs and often includes invented function names or nonexistent libraries. By grounding each plan step in retrieved documentation, the output is consistent, specific, and tied to real patterns.

**Why pre-generated knowledge base docs?**
Writing the knowledge base by hand means the retrieval system has high-quality, structured material to work with. Scraping real docs or using arbitrary web content would introduce noise and make retrieval less reliable within the scope of this project.

**Why keyword-based retrieval instead of embeddings?**
A simple inverted index with word-count scoring is transparent, fast, and easy to evaluate. Embedding-based semantic search would improve retrieval quality but adds significant complexity and infrastructure. For a focused knowledge base, keyword retrieval is sufficient and the trade-off is worth it.

**Why CLI instead of a web interface?**
The planner's value is in the quality of its reasoning, not its UI. A CLI keeps the project focused on the AI pipeline and avoids frontend complexity that would consume time without adding to the core system.

**Why Gemini (gemma-3-27b-it)?**
The project starter was built around the Google Gemini API, and it provides a free tier sufficient for development and testing. The model handles instruction-following well, which is important for strict RAG prompts that require refusals when context is insufficient.

---

## Testing Summary

> **Note:** Fill this in after running `evaluation.py` and testing the full pipeline.

**Retrieval evaluation**
- Hit rate: [e.g. 0.75 — fill in your actual result]
- Queries where retrieval failed: [list them]
- What improved hit rate: [e.g. stripping punctuation from tokens, lowercasing]

**Plan quality observations**
- What worked well: [e.g. auth and database phases were well-grounded]
- What didn't work: [e.g. deployment phase had weak doc coverage]
- Edge cases: [e.g. very vague goals produced shallow plans]

**What I learned**
[Fill in after testing — what surprised you, what you'd do differently]

---

## Reflection

> **Note:** Write this last, in your own words, after you've built and tested the system.

[Reflect on: What did building this teach you about how RAG works in practice? What surprised you about the gap between retrieval and generation? How does grounding AI output in real sources change what you trust about the answer? What would you add if you had more time?]

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.9+ |
| LLM | Google Gemini (gemma-3-27b-it) |
| Retrieval | Keyword inverted index (custom) |
| Knowledge base | Hand-authored `.md` files |
| Evaluation | Custom hit-rate harness |
| Interface | CLI |
