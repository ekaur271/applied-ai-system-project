"""
Project Planner — handles the planning conversation and plan generation.

Flow:
1. Ask the user 9 planning questions
2. Assemble answers into a context block
3. LLM decomposes the project into phases
4. For each phase, retrieve relevant docs via RAG
5. LLM generates grounded steps per phase
6. Output the full structured plan
"""

import logging

logger = logging.getLogger(__name__)

QUESTIONS = [
    ("problem",   "What's the one problem this solves?"),
    ("users",     "Who has this problem and how do they deal with it today?"),
    ("core_loop", "Walk me through what a user actually does in your app, step by step."),
    ("mvp",       "What's the simplest version that proves your idea works?"),
    ("risks",     "What's the riskiest part — what are you most unsure how to build?"),
    ("cuts",      "What could you cut if you ran out of time?"),
    ("technical", "What does your app need to be able to do technically? (e.g. store data, send emails, call an API, process files)"),
    ("stack",     "What tools, languages, or frameworks are you planning to use? (say 'suggest one' if unsure)"),
    ("done",      "What does done look like to you? How will you know it works?"),
]


def ask_planning_questions():
    """
    Walk the user through the 9 planning questions.
    Returns a dict mapping question keys to user answers.
    """
    print("\n" + "=" * 60)
    print("DocuBot Project Planner")
    print("=" * 60)
    print("\nLet's figure out what you're building.")
    print("Answer each question as honestly as you can — even rough answers help.\n")

    answers = {}
    for i, (key, question) in enumerate(QUESTIONS, 1):
        print(f"Q{i}: {question}")
        answer = input("    > ").strip()
        answers[key] = answer if answer else "Not specified"
        print()

    return answers


def assemble_context(answers):
    """
    Formats the user's answers into a structured context block
    that gets passed to the LLM for plan generation.
    """
    labels = {
        "problem":   "Problem being solved",
        "users":     "Target users and current alternatives",
        "core_loop": "Core user flow",
        "mvp":       "MVP definition",
        "risks":     "Technical risks and unknowns",
        "cuts":      "Features that can be cut",
        "technical": "Technical requirements",
        "stack":     "Tech stack",
        "done":      "Definition of done",
    }

    lines = ["PROJECT CONTEXT", "-" * 40]
    for key, label in labels.items():
        lines.append(f"{label}: {answers.get(key, 'Not specified')}")

    return "\n".join(lines)


def show_summary_and_confirm(answers):
    """
    Shows the user a summary of their answers and asks if they're ready
    to generate the plan.
    """
    print("\n" + "=" * 60)
    print("Here's what you told me:")
    print("=" * 60)
    print(f"  Problem:   {answers['problem']}")
    print(f"  MVP:       {answers['mvp']}")
    print(f"  Stack:     {answers['stack']}")
    print(f"  Done when: {answers['done']}")
    print()

    choice = input("Ready to generate your plan? (yes / no): ").strip().lower()
    return choice in ("yes", "y")


def generate_plan(context, bot, llm_client):
    """
    Orchestrates the full plan generation pipeline:
    1. Decompose project into phases
    2. For each phase, retrieve relevant docs
    3. Generate grounded steps per phase
    4. Return the assembled plan as a string
    """
    logger.info("Starting plan generation")
    print("\nGenerating your plan...\n")

    # Step 1: decompose into phases
    print("  [1/3] Breaking your project into phases...")
    phases = llm_client.decompose_into_phases(context)
    logger.info("Decomposed into %d phases: %s", len(phases), phases)

    if not phases:
        return "Could not decompose your project into phases. Please try again with more detail."

    # Step 2 + 3: for each phase, retrieve docs and generate steps
    print("  [2/3] Retrieving relevant documentation for each phase...")
    plan_sections = []

    for i, phase in enumerate(phases, 1):
        logger.info("Processing phase %d: %s", i, phase)

        # Retrieve docs relevant to this phase
        snippets = bot.retrieve(f"{phase} {context}", top_k=3)

        # Generate grounded steps using retrieved snippets
        steps = llm_client.generate_phase_steps(phase, context, snippets)
        plan_sections.append(f"## Phase {i}: {phase}\n\n{steps}")

    print("  [3/3] Assembling your plan...\n")

    plan = "\n\n".join(plan_sections)
    logger.info("Plan generation complete")
    return plan


def run_planner(bot, llm_client):
    """
    Main entry point for the planner mode.
    Called from main.py.
    """
    if llm_client is None:
        print("\nThe planner requires a Gemini API key. Please set GEMINI_API_KEY in your .env file.\n")
        return

    # Stage 1: planning conversation
    answers = ask_planning_questions()

    # Confirm before generating
    if not show_summary_and_confirm(answers):
        print("\nNo problem — come back when you're ready.\n")
        return

    # Stage 2: plan generation
    context = assemble_context(answers)
    plan = generate_plan(context, bot, llm_client)

    # Output
    print("=" * 60)
    print("YOUR PROJECT PLAN")
    print("=" * 60)
    print()
    print(plan)
    print()
