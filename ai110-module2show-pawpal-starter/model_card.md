# Model Card — PawPal+ AI Health Check

## System Overview

**Base project:** PawPal+ (Module 2 — AI110)
**Extension:** AI-powered pet health analysis using RAG + agentic workflow
**Model used:** Claude Haiku (`claude-haiku-4-5-20251001`) via Anthropic API
**Interface:** Streamlit web app — Health Check tab

---

## AI Collaboration

I used Claude throughout this project to help me figure out how to structure things I hadn't built before and to write code I could then read through and understand.

**One instance where AI was helpful:**
I wanted the health check to show each step as it was happening instead of just showing a final result, but wasn't sure how to do that in Streamlit without blocking. Claude suggested using a Python generator — `yield` each step as it finishes and `return` the final result — and that worked really cleanly. I don't think I would've figured that out on my own quickly.

**One instance where AI's suggestion was flawed:**
Claude wrote the prompt to tell the model to return plain JSON with no markdown formatting. When I ran it for the first time it came back wrapped in code fences anyway and the whole thing crashed with a JSON parse error. The fix was easy once I knew what was wrong, but it was a wake-up call that you can't just tell a model to do something and trust that it will — you have to handle whatever it actually sends back.

---

## Intended Use

- **Primary use:** Informational first-pass triage for pet owners who notice something unusual about their pet's behavior or health
- **Not intended for:** Replacing professional veterinary diagnosis or treatment decisions
- **Supported species:** Dogs and cats (with species-specific knowledge retrieval)

---

## Limitations and Biases

- **The knowledge base is really small.** I only wrote 5 markdown files covering basic dog and cat symptoms. If someone types in something unusual, the system has no relevant docs to pull from and just relies on what Claude already knows.
- **Keyword matching breaks down with natural language.** "My dog won't eat" might not score well against a chunk that says "loss of appetite" because the words don't overlap. It works better when people use more specific language.
- **No memory between sessions.** Every health check starts from scratch — the system has no idea if the same pet has shown the same symptom multiple times.
- **Haiku isn't a medical model.** It's a small general-purpose model. The few-shot examples shape its tone but it doesn't have real veterinary expertise.
- **Only covers dogs and cats.** Owners of other pets will get responses based on Claude's general knowledge only.

---

## Misuse Risks and Mitigations

**Risk:** An owner uses this tool instead of seeking veterinary care, delays treatment for a serious condition, and the pet is harmed.

**Mitigations:**
- A keyword guardrail independently escalates severity to "high" and forces a vet referral for dangerous terms (blood, seizure, urinate, collapse, poison, obstruction) regardless of what the model outputs
- Every response includes a disclaimer: "This tool is for informational purposes only and does not replace professional veterinary advice"
- The recommendation framing is always "contact your vet" rather than "your pet has X"
- The system never claims diagnostic certainty

---

## Testing and Reliability

**Evaluation harness:** `test_health_harness.py` — 9 predefined test cases

| Test | Description | Result |
|---|---|---|
| 1 | Dog eating grass + vomiting | PASS — low severity, no vet |
| 2 | Cat not eating 2 days | PASS — high severity, vet=True |
| 3 | Dog scratching ears | PASS — medium severity |
| 4 | Dog vomiting blood (guardrail) | PASS — high severity forced, vet=True |
| 5 | Cat can't urinate (guardrail) | PASS — high severity forced, vet=True |
| 6 | Empty input | PASS — rejected before API call |
| 7 | Gibberish input | PASS — rejected before API call |
| 8 | Off-topic input (car noise) | PASS — rejected before API call |
| 9 | Vague input ("dog seems off") | PASS — valid low-severity response |

**Result: 9/9 passed**

**Logging:** All queries are written to `health_agent.log` with pet name, species, symptom category, severity, and vet_required flag.

---

## What Surprised Me While Testing

The first surprise was how fast things broke on the first real run. I had tested the imports and confirmed the API key — and then the JSON parser immediately crashed because the model sent back code fences instead of plain JSON. I hadn't thought about that at all. It made me realize testing individual pieces doesn't tell you much about whether the whole thing works end-to-end.

The second surprise was that the simplest guardrails worked the best. The empty input and off-topic checks both passed instantly without touching the API at all — just a few lines of string checking. Meanwhile getting the model to return clean JSON took multiple tries.

Test 9 (vague input: "my dog seems off today") also surprised me — I expected it to fail but it still came back with a reasonable response. The examples in the prompt were doing more work than I realized.

---

## What This Taught Me About AI and Problem-Solving

This was my first time building something where an LLM is actually part of a real working app. The thing that stood out most is how much of the work has nothing to do with the model itself — writing the knowledge docs, structuring the retrieval, deciding what gets validated in code vs. what gets decided by the AI. The model call is almost the easy part. I came in thinking AI engineering was mostly about prompting. I'm leaving thinking it's mostly about everything around the prompt.
