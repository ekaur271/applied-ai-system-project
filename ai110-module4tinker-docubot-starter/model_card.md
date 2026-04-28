# SWE Mentor — Model Card

---

## 1. System Overview

**What is SWE Mentor trying to do?**
SWE Mentor takes a plain-language description of a software project and generates a structured, phase-by-phase implementation plan grounded in retrieved software engineering best-practice documentation. It extends the original DocuBot Q&A assistant into a full agentic planning system that retrieves relevant context before generating any output.

**What inputs does SWE Mentor take?**
- A paragraph from the user describing their project (goal, users, MVP, stack, definition of done)
- A folder of 17 markdown documentation files covering SWE best practices (auth, database, API design, deployment, etc.)
- A `GEMINI_API_KEY` environment variable for LLM access

**What outputs does SWE Mentor produce?**
A structured 4–6 phase implementation plan where each phase contains 3–5 numbered steps with beginner-friendly rationale. Steps are grounded in retrieved documentation; steps not covered by docs are flagged as "Research needed: [topic]" rather than hallucinated.

---

## 2. Retrieval Design

**How does your retrieval system work?**

- **Indexing:** At startup, each markdown file is tokenized by splitting on non-word characters (lowercased). An inverted index maps each token to the list of files that contain it.
- **IDF weighting:** Each token is assigned an IDF score — `total_documents / document_frequency`. Rare, domain-specific tokens (e.g. "jwt", "middleware") score much higher than common words (e.g. "how", "use", "the").
- **Query expansion:** Before retrieval, the user's query is rewritten by Gemini into precise technical lowercase keywords (e.g. "make people log in" → "authentication session management jwt flask"). This bridges the vocabulary gap between beginner phrasing and technical documentation terms.
- **Scoring:** For each candidate document, its score is the sum of IDF weights for all query tokens that appear in that document.
- **Selection:** The top-k highest-scoring documents are returned (default k=5 for the planner).

**What tradeoffs did you make?**
- Keyword retrieval over embedding-based semantic search: simpler, faster, fully transparent, and sufficient for a focused knowledge base. Embedding retrieval would improve performance on paraphrased or synonymous queries but adds infrastructure complexity.
- IDF over equal word weighting: measurably improved hit rate (from 0.00 to 0.73) because domain-specific words dominate scores over filler words.
- Single retrieval pass over per-phase retrieval: a per-phase approach would produce more targeted snippets per step, but exhausted API rate limits in practice. A single pass with top-5 docs feeds the full plan generation in one LLM call.

---

## 3. Use of the LLM (Gemini)

**When does SWE Mentor call the LLM and when does it not?**

- **Naive LLM mode:** Sends the user's question directly to Gemini with the full corpus text. No retrieval. Fast but ungrounded — answers can be generic or invented.
- **Retrieval only mode:** No LLM. Scores and returns the top matching document snippets as plain text. Accurate but not synthesized — the user reads raw docs.
- **RAG mode:** Retrieves top-k snippets first, then passes them to Gemini with a strict instruction to answer only from the provided context and cite which files it used.
- **Project Planner mode:** Calls the LLM three times — once for query expansion, once for retrieval expansion (inside `retrieve()`), and once for full plan generation from retrieved snippets.

**What instructions do you give the LLM to keep it grounded?**
- The plan generation prompt includes a complete few-shot example (a to-do app) to anchor format and tone
- The model is told to use ONLY the provided documentation — no outside knowledge
- Any step not covered by retrieved docs must be written as "Research needed: [topic]" rather than fabricated
- The RAG prompt requires the model to cite which files it relied on and reply "I do not know based on the docs I have" if snippets are insufficient

---

## 4. Experiments and Comparisons

| Query | Naive LLM | Retrieval only | RAG | Notes |
|---|---|---|---|---|
| How do I set up JWT authentication? | Helpful but generic — no citation, steps vary between runs | Returns auth.md content directly | Grounded, cites auth.md, consistent | RAG wins on consistency |
| What environment variables should I never commit? | Correct answer but no source | Returns environment-and-config.md | Same answer with file citation | All three acceptable, RAG most trustworthy |
| How do I design REST API endpoints? | Plausible but sometimes invents endpoint names | Returns api-design.md snippets | Synthesized from api-design.md | Naive LLM is risky here |
| How do I make my app scalable? | Generic buzzwords, no actionable steps | Returns scalability.md verbatim | Structured answer from scalability.md | Retrieval + RAG both outperform naive |

**What patterns did you notice?**
- Naive LLM looks impressive on simple, well-known topics but varies between runs and cannot cite sources — it's untrustworthy for anything domain-specific
- Retrieval only is reliable and auditable but outputs raw markdown the user must read themselves
- RAG is clearly better when the question maps cleanly to a doc; it synthesizes a readable answer with citations. It fails when the query vocabulary doesn't match doc vocabulary, which is where query expansion helps

---

## 5. Failure Cases and Guardrails

**Failure case 1: vocabulary mismatch**
- Question: "How do I make people log in?"
- What the system did: retrieval returned no candidates because "log in" doesn't match any index token; plan was generated with "No documentation retrieved" as context, producing only "Research needed" flags
- What should have happened: `auth.md` and `environment-and-config.md` should have been retrieved
- Fix applied: LLM query expansion now rewrites queries into technical keywords before retrieval

**Failure case 2: retrieval pulls generic docs for unrelated queries**
- Question: "How do I integrate an AI model?"
- What the system did: returned `requirements-and-planning.md` and `design-patterns.md` instead of `ai-integration.md` because those docs share many general SWE terms
- What should have happened: `ai-integration.md` should be the top result
- Root cause: general-purpose docs have high token overlap with many queries; IDF partially mitigates this but doesn't eliminate it

**When should SWE Mentor say "I do not know based on the docs I have"?**
- When the retrieved snippets contain no relevant content for the user's specific question
- When the user asks about a technology or framework not covered in the knowledge base (e.g. specific ORM internals, mobile-specific deployment)

**What guardrails did you implement?**
- Strict prompt instruction: "Using ONLY the documentation below" with explicit "Research needed" fallback
- Empty retrieval handling: if no candidates are found, `snippets` is empty and the model is told "No documentation retrieved"
- Query expansion fallback: if the LLM call fails (503, timeout), the original query is used as a safe default
- Model verification at startup: `_verify_model()` confirms the API key and model are reachable before accepting user input

---

## 6. Limitations and Future Improvements

**Current limitations**

1. Keyword retrieval misses semantic matches — "make people log in" and "user authentication" mean the same thing but score differently; query expansion compensates but is an imperfect proxy
2. Knowledge base is static and hand-authored — the 17 docs cover common patterns but any technology not represented produces "Research needed" flags rather than real guidance
3. Single retrieval pass — the planner retrieves one set of docs for the whole description rather than per-phase retrieval; a complex multi-domain project may get docs tuned to one aspect and miss others
4. No persistence — plans are printed to the terminal only; there is no way to save, revisit, or iterate on a plan

**Future improvements**

1. Scaffold generation — take the generated plan and automatically create the folder structure, starter files, and a skeleton README for the described project
2. Per-phase retrieval — retrieve a separate set of docs for each plan phase to improve grounding precision for multi-domain projects
3. Embedding-based retrieval — replace the keyword index with vector embeddings to handle paraphrased queries and synonyms without relying on query expansion

---

## 7. Responsible Use

**Where could this system cause real-world harm if used carelessly?**
A beginner developer who follows the generated plan without verification could implement insecure patterns if the retrieved docs are incomplete or if the LLM fills gaps with plausible but incorrect steps. The "Research needed" flag is only as reliable as the knowledge base coverage — topics not in the docs are flagged, but topics covered incorrectly or incompletely could produce subtly wrong guidance. Over-trusting AI-generated plans without code review or testing is the primary risk.

**What instructions would you give real developers who want to use SWE Mentor safely?**
- Treat the generated plan as a starting point, not a specification — verify each step against official documentation before implementing
- If a step looks unfamiliar or surprising, look it up; "Research needed" flags are honest but absence of a flag is not a guarantee of correctness
- Expand the knowledge base with your specific stack's official docs before using the planner for a production project
- Run `evaluation.py` after any changes to the knowledge base or retrieval logic to verify hit rate hasn't regressed

---
