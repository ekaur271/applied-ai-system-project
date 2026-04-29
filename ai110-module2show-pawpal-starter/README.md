# PawPal+ with AI Health Check

**PawPal+** is a smart pet care scheduling app extended with an AI-powered health analysis system. The original app helps busy pet owners build optimized daily schedules for their pets. This version adds a 4-step agentic health checker that uses Retrieval-Augmented Generation (RAG) to analyze owner observations, retrieve relevant pet health knowledge, and return a severity-rated recommendation — all with observable intermediate steps.

---

## Base Project

**Original project:** PawPal+ (Module 2 — AI110)

PawPal+ was a Streamlit-based pet care scheduler that automatically built daily care schedules around owner availability, pet needs, and task priorities. It featured priority-based scheduling, conflict detection across multiple pets, day load balancing, task batching, and a full dark-mode dashboard. The system had no AI component — all logic was rule-based Python algorithms.

---

## What's New

| Feature | Description |
|---|---|
| **RAG Health Retrieval** | A knowledge base of 5 species-specific markdown documents (dogs/cats × digestive/behavioral + common symptoms) is chunked and scored at query time. The top matching chunks are passed as context to Claude. |
| **Agentic Workflow** | A 4-step agent loop (Classify → Retrieve → Analyze → Validate) with each step's result shown live in the UI. |
| **Few-Shot Specialization** | The analysis prompt includes 3 labeled examples that constrain Claude's tone and output format — caring but clinically accurate, structured JSON. |
| **Guardrails** | Input validation rejects empty, gibberish, and off-topic observations before any API call. Keyword-based escalation forces high severity and vet referral when dangerous symptoms are detected. All queries are logged to `health_agent.log`. |
| **Test Harness** | `test_health_harness.py` runs 9 predefined inputs and prints a pass/fail summary. |

---

## System Architecture

```
Owner Input (Streamlit UI)
        │
        ▼
┌─────────────────────────────────────────────────────┐
│                  Health Agent (health_agent.py)      │
│                                                      │
│  Step 1: Classify                                    │
│    └─ Claude Haiku → symptom category               │
│         (digestive / behavioral / physical)          │
│                                                      │
│  Step 2: Retrieve                                    │
│    └─ HealthRetriever → keyword score chunks        │
│         from pet_health_docs/ (5 .md files)          │
│         Species boost: dog/cat-specific docs ranked  │
│                                                      │
│  Step 3: Analyze                                     │
│    └─ Claude Haiku + retrieved context +            │
│         few-shot examples → JSON response            │
│         {likely_cause, severity, recommendation,     │
│          vet_required}                               │
│                                                      │
│  Step 4: Validate                                    │
│    └─ Keyword guardrail check                       │
│         high-severity keywords → force vet=true      │
│         Log all queries to health_agent.log          │
└─────────────────────────────────────────────────────┘
        │
        ▼
  Streamlit UI — displays steps live + final analysis
        │
        ▼
  Existing PawPal+ Schedule Tab (unchanged)
```

![System Architecture](../assets/mermaid-diagram-2026-04-29-194512.png)

**Data flow:** Owner types an observation → agent classifies it → retriever pulls relevant health doc chunks → Claude analyzes using context + few-shot examples → validator applies safety guardrails → result shown with severity badge, recommendation, and sources.

---

## Setup

```bash
# 1. Clone the repo and enter the project folder
git clone https://github.com/ekaur271/applied-ai-system-project.git
cd applied-ai-system-project/ai110-module2show-pawpal-starter

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your Anthropic API key
cp .env.example .env           # then open .env and add your key
# ANTHROPIC_API_KEY=sk-ant-...

# 5. Run the app
streamlit run app.py
```

> The `.env` file is gitignored. Never commit your API key.

---

## Sample Interactions

### 1. Mild digestive symptom
**Input:** `my dog has been eating grass and throwing up this morning`

```
Step 1: Classify Symptom        → Category: digestive
Step 2: Retrieve Knowledge      → 4 chunks from dogs_digestive.md, dogs_behavioral.md
Step 3: Analyze with Claude     → Severity: low
Step 4: Validate Output         → vet_required=False | guardrails applied

MEDIUM SEVERITY
Likely Cause: Mochi is likely experiencing mild stomach upset. Dogs eat grass to
induce vomiting as a self-regulating behavior to clear gastrointestinal irritation.

Recommendation: Monitor for 24 hours. Ensure fresh water is available. If vomiting
continues more than twice or Mochi seems lethargic, contact your vet.
```

---

### 2. High severity — guardrail triggered
**Input:** `my dog is vomiting blood and seems very weak`

```
Step 1: Classify Symptom        → Category: digestive
Step 2: Retrieve Knowledge      → 4 chunks from dogs_digestive.md, common_symptoms.md
Step 3: Analyze with Claude     → Severity: high
Step 4: Validate Output         → keyword 'blood' detected → vet_required=True forced

HIGH SEVERITY
Likely Cause: Vomiting blood combined with weakness is a serious emergency sign
that may indicate internal bleeding, severe gastritis, or poisoning.

Recommendation: Seek veterinary care immediately. ⚠️ Please contact your
veterinarian immediately.
```

---

### 3. Off-topic input — rejected before API call
**Input:** `my car won't start and makes a clicking noise`

```
⚠️ This doesn't seem to be about a pet's health. Please describe a symptom or
behavior you've noticed in your pet.
```
*(No API call made — rejected by keyword guardrail)*

---

## Design Decisions

**Why RAG instead of just prompting Claude directly?**
Sending raw owner observations to Claude with no context produces generic answers. By retrieving species-specific chunks first, the response is grounded in structured pet health knowledge. This also makes the system auditable — the UI shows exactly which source files were used.

**Why keyword retrieval instead of embeddings?**
For a knowledge base of 5 small markdown files, TF-IDF-style keyword scoring is fast, transparent, and requires no vector database setup. The species boost (dog/cat-specific docs score +2) ensures the right documents rank first without any ML overhead.

**Why 4 separate agent steps instead of one prompt?**
Breaking the workflow into Classify → Retrieve → Analyze → Validate makes each step observable and testable. The classification step lets us route to species-specific docs. The validation step applies safety rules independently of the LLM, so guardrails can't be overridden by a model output.

**Why Claude Haiku?**
Fast and cheap for a real-time UI. The few-shot examples and structured JSON output format compensate for the smaller model's lower instruction-following reliability.

---

## Testing Summary

### Evaluation Harness (`test_health_harness.py`)
**Result: 9/9 passed**

| Test | Input | Expected | Result |
|---|---|---|---|
| 1 | Dog eating grass + vomiting | low/medium, no vet | PASS — low |
| 2 | Cat not eating 2 days | high, vet required | PASS — high, vet=True |
| 3 | Dog scratching ears | medium, no vet | PASS — medium |
| 4 | Dog vomiting blood | high, vet (guardrail) | PASS — high, vet=True |
| 5 | Cat can't urinate | high, vet (guardrail) | PASS — high, vet=True |
| 6 | Empty input | error | PASS |
| 7 | Gibberish input | error | PASS |
| 8 | Off-topic (car noise) | error | PASS |
| 9 | Vague input ("dog seems off") | any valid response | PASS — low |

**What worked:** Severity classification was consistent across runs. The keyword guardrail correctly escalated "blood" and "urinate" to high severity without relying on the LLM. Input validation caught all three edge case types before making any API call.

**What didn't work initially:** Claude returned JSON wrapped in markdown fences despite being told not to — fixed by stripping fences before `json.loads()`. The gibberish test initially passed through to Claude and produced a confused output — fixed by adding a real-word count check.

**What I'd add next:** Confidence scoring on the classification step, and tests for multi-symptom observations (e.g., "my dog is vomiting and limping").

### Existing PawPal+ Tests (`tests/test_pawpal.py`)
43 pytest tests covering all scheduling logic — priority ordering, busy block avoidance, conflict detection, batching, and JSON persistence. Run with:
```bash
python -m pytest tests/test_pawpal.py -v
```

---

## Reflection

### How I Used AI During Development

I used Claude as a collaborator throughout this project — for design, implementation, and debugging.

**One instance where AI was helpful:** When I described wanting a "4-step agent that shows its work," Claude immediately structured the generator pattern (`yield AgentStep` → `return HealthAnalysis`) which made streaming intermediate steps to the Streamlit UI clean and testable. I wouldn't have reached that pattern as quickly on my own.

**One instance where AI's suggestion was flawed:** Claude initially wrote the analysis prompt with `"Return only valid JSON, no markdown fences"` — but then returned markdown-fenced JSON anyway when actually called. The fix (stripping fences before parsing) was simple, but it highlighted that model instruction-following is unreliable and output parsing always needs defensive handling.

### Limitations

- **Knowledge base is static and small.** The 5 markdown files cover common symptoms but can't replace a real veterinary database. Unusual or rare symptoms will fall back to Claude's general knowledge with no retrieved context.
- **Keyword retrieval misses semantic matches.** A query like "Mochi won't touch her bowl" won't score against "loss of appetite" because the words don't overlap. Embedding-based retrieval would fix this.
- **No memory across sessions.** Each health check is independent. The system can't notice patterns like "this dog has shown digestive symptoms 3 times this week."
- **Haiku is not a medical model.** The system is informational only. All outputs include a disclaimer and the system always defers to veterinary professionals for serious cases.

### Could this be misused?

An owner could use the tool as a substitute for a vet, delaying care for a serious condition. The system mitigates this by always appending a disclaimer, forcing vet referrals for high-severity keywords, and never claiming diagnostic certainty. The recommendation framing is deliberately "contact your vet" rather than "your pet has X."

---

## Project Structure

```
ai110-module2show-pawpal-starter/
├── app.py                    # Streamlit UI — Schedule + Health Check tabs
├── pawpal_system.py          # Original scheduling backend (unchanged)
├── health_agent.py           # 4-step agentic health analysis loop
├── health_retriever.py       # RAG retriever — keyword chunk scoring
├── test_health_harness.py    # Evaluation harness (9 test cases)
├── pet_health_docs/          # RAG knowledge base
│   ├── dogs_digestive.md
│   ├── dogs_behavioral.md
│   ├── cats_digestive.md
│   ├── cats_behavioral.md
│   └── common_symptoms.md
├── tests/
│   └── test_pawpal.py        # 43 original pytest tests
├── requirements.txt
├── .env                      # API key (gitignored)
└── .streamlit/
    └── config.toml           # Dark mode theme
```

---

## Loom Walkthrough

*(Add your Loom link here before submitting)*

---

*This project does not provide veterinary advice. Always consult a licensed veterinarian for your pet's health.*
