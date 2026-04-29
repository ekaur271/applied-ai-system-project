"""
PawPal Health Agent — 4-step agentic loop:
  Step 1: Classify symptom category (digestive / behavioral / physical / unknown)
  Step 2: Retrieve relevant chunks from pet_health_docs via RAG
  Step 3: Analyze using Claude with retrieved context + few-shot examples
  Step 4: Validate — enforce vet warning for high-severity outputs

Each step yields an observable AgentStep so the UI can show progress.
"""

import os
import json
import logging
from dataclasses import dataclass, field
from typing import Generator

import anthropic
from dotenv import load_dotenv
from health_retriever import HealthRetriever

load_dotenv()

logging.basicConfig(
    filename="health_agent.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

FEW_SHOT_EXAMPLES = """
Example 1:
Observation: "my dog keeps eating grass and then throwing up"
Species: dog
Analysis:
{
  "likely_cause": "Mild stomach upset. Dogs eat grass to induce vomiting and clear gastrointestinal irritation. Occasional grass eating followed by vomiting is a normal self-regulating behavior.",
  "severity": "low",
  "recommendation": "Monitor for 24 hours. Ensure fresh water is available. If vomiting continues more than twice or the dog seems lethargic, schedule a vet visit.",
  "vet_required": false
}

Example 2:
Observation: "my cat hasn't eaten anything in two days"
Species: cat
Analysis:
{
  "likely_cause": "Prolonged food refusal in cats is a serious concern. Cats that don't eat for more than 24-48 hours are at risk of hepatic lipidosis (fatty liver disease), even if the underlying cause is stress or a new food.",
  "severity": "high",
  "recommendation": "See a veterinarian today. Do not wait to see if the cat resumes eating on its own.",
  "vet_required": true
}

Example 3:
Observation: "my dog is scratching its ears a lot and shaking its head"
Species: dog
Analysis:
{
  "likely_cause": "Frequent head shaking and ear scratching typically indicate an ear infection or ear mites. A dark discharge or odor from the ears further supports this.",
  "severity": "medium",
  "recommendation": "Schedule a vet appointment within 24-48 hours. Avoid inserting anything into the ear canal at home.",
  "vet_required": false
}
"""

CLASSIFY_PROMPT = """You are a pet health assistant. Given a symptom observation, classify it into one of these categories:
- digestive (vomiting, diarrhea, not eating, drinking too much, grass eating, bloating)
- behavioral (lethargy, hiding, aggression, excessive vocalization, personality change)
- physical (limping, scratching, skin issues, ear problems, grooming changes)
- unknown

Respond with only one word from the list above.

Observation: {observation}"""

ANALYZE_PROMPT = """You are a caring but clinically accurate pet health assistant. Use the retrieved knowledge base excerpts below and the few-shot examples to analyze the owner's observation.

--- KNOWLEDGE BASE ---
{context}

--- FEW-SHOT EXAMPLES ---
{examples}

--- TASK ---
Pet name: {pet_name}
Species: {species}
Owner's observation: {observation}

Respond with a JSON object containing exactly these keys:
- likely_cause (string): plain-language explanation of what is probably happening
- severity (string): one of "low", "medium", or "high"
- recommendation (string): what the owner should do next
- vet_required (boolean): true if the owner should see a vet

Return only valid JSON, no markdown fences."""


@dataclass
class AgentStep:
    step_number: int
    name: str
    detail: str
    result: str = ""


@dataclass
class HealthAnalysis:
    pet_name: str
    species: str
    observation: str
    symptom_category: str
    sources: list = field(default_factory=list)
    likely_cause: str = ""
    severity: str = ""
    recommendation: str = ""
    vet_required: bool = False
    steps: list = field(default_factory=list)
    error: str = ""


def run_health_check(
    pet_name: str,
    species: str,
    observation: str,
) -> Generator[AgentStep, None, HealthAnalysis]:
    """
    Generator that yields AgentStep objects as each step completes,
    then returns a HealthAnalysis as the final StopIteration value.
    Usage:
        gen = run_health_check(...)
        steps = []
        try:
            while True:
                step = next(gen)
                steps.append(step)
        except StopIteration as e:
            result = e.value
    """
    analysis = HealthAnalysis(
        pet_name=pet_name, species=species, observation=observation,
        symptom_category="", steps=[]
    )

    # guard: reject empty or too-short input
    if not observation or len(observation.strip()) < 5:
        analysis.error = "Please describe a specific symptom or observation (at least 5 characters)."
        logging.warning("Rejected empty/short observation for %s", pet_name)
        return analysis

    # guard: reject gibberish (observation must contain at least 2 real words)
    real_words = [w for w in observation.strip().split() if w.isalpha() and len(w) > 1]
    if len(real_words) < 2:
        analysis.error = "Observation doesn't look like a valid description. Please use plain words to describe what you noticed."
        logging.warning("Rejected gibberish observation for %s", pet_name)
        return analysis

    # guard: reject off-topic input (must contain at least one pet/health-related word)
    PET_KEYWORDS = {
        "dog", "cat", "pet", "puppy", "kitten", "animal", "fur", "paw",
        "eat", "eating", "drink", "drinking", "vomit", "vomiting", "sick",
        "lethargic", "tired", "scratch", "scratching", "limp", "limping",
        "poop", "pee", "urine", "stool", "diarrhea", "bloa", "seizure",
        "fur", "coat", "bark", "meow", "hide", "hiding", "appetite",
        "food", "water", "grass", "throwing", "stomach", "pain", "blood",
        "breath", "breathe", "cough", "sneeze", "eye", "nose", "ear",
        "tail", "leg", "belly", "mouth", "teeth", "gum", "weight",
    }
    obs_words = set(observation.lower().split())
    if not obs_words & PET_KEYWORDS:
        analysis.error = "This doesn't seem to be about a pet's health. Please describe a symptom or behavior you've noticed in your pet."
        logging.warning("Rejected off-topic observation for %s: '%s'", pet_name, observation[:60])
        return analysis

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    retriever = HealthRetriever()

    # ── Step 1: Classify ─────────────────────────────────────────────────────
    step1 = AgentStep(1, "Classify Symptom", f'Categorizing: "{observation}"')
    yield step1

    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": CLASSIFY_PROMPT.format(observation=observation)}],
        )
        category = resp.content[0].text.strip().lower()
        if category not in ("digestive", "behavioral", "physical"):
            category = "unknown"
    except Exception as e:
        category = "unknown"
        logging.error("Classification failed: %s", e)

    step1.result = f"Category: {category}"
    analysis.symptom_category = category
    analysis.steps.append(step1)

    # ── Step 2: Retrieve ─────────────────────────────────────────────────────
    step2 = AgentStep(2, "Retrieve Knowledge", f"Searching {species} health docs for '{category}' symptoms")
    yield step2

    query = f"{species} {category} {observation}"
    results = retriever.retrieve(query, species=species, top_k=4)
    sources = retriever.get_sources(results)
    context = "\n\n---\n\n".join(f"[{fname}]\n{chunk}" for fname, chunk in results)

    if not results:
        context = "No specific documentation found. Use general veterinary knowledge."

    step2.result = f"Retrieved {len(results)} chunks from: {', '.join(sources) if sources else 'general knowledge'}"
    analysis.sources = sources
    analysis.steps.append(step2)

    # ── Step 3: Analyze ──────────────────────────────────────────────────────
    step3 = AgentStep(3, "Analyze with Claude", "Generating health insight using retrieved context")
    yield step3

    prompt = ANALYZE_PROMPT.format(
        context=context,
        examples=FEW_SHOT_EXAMPLES,
        pet_name=pet_name,
        species=species,
        observation=observation,
    )

    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        # strip markdown fences if model wraps output despite instructions
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        parsed = json.loads(raw)
        analysis.likely_cause = parsed.get("likely_cause", "")
        analysis.severity = parsed.get("severity", "low")
        analysis.recommendation = parsed.get("recommendation", "")
        analysis.vet_required = parsed.get("vet_required", False)
        step3.result = f"Severity: {analysis.severity}"
    except Exception as e:
        analysis.error = f"Analysis failed: {e}"
        step3.result = "Analysis failed"
        logging.error("Analysis failed for %s: %s", pet_name, e)

    analysis.steps.append(step3)

    # ── Step 4: Validate ─────────────────────────────────────────────────────
    step4 = AgentStep(4, "Validate Output", "Checking severity and enforcing guardrails")
    yield step4

    HIGH_SEVERITY_KEYWORDS = [
        "blood", "bloat", "collapse", "seizure", "breathing",
        "urinate", "obstruction", "emergency", "poison", "toxic"
    ]
    if any(kw in observation.lower() for kw in HIGH_SEVERITY_KEYWORDS):
        analysis.severity = "high"
        analysis.vet_required = True

    if analysis.severity == "high":
        analysis.vet_required = True
        if "veterinarian" not in analysis.recommendation.lower() and "vet" not in analysis.recommendation.lower():
            analysis.recommendation += " ⚠️ Please contact your veterinarian immediately."

    step4.result = f"vet_required={analysis.vet_required} | guardrails applied"
    analysis.steps.append(step4)

    logging.info(
        "HealthCheck | pet=%s species=%s category=%s severity=%s vet_required=%s",
        pet_name, species, category, analysis.severity, analysis.vet_required,
    )

    return analysis
