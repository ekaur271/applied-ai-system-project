"""
Project Planner — handles the planning conversation and plan generation.

Flow:
1. Ask the user 9 planning questions
2. Assemble answers into one coherent project paragraph
3. Retrieve the most relevant docs using that paragraph as the query
4. One LLM call: project paragraph + retrieved docs → full structured plan
5. Output the plan
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


def assemble_paragraph(answers):
    """
    Turns the user's 9 answers into one coherent project description paragraph.
    This is used as both the retrieval query and the LLM context.
    """
    return (
        f"I want to build something that solves this problem: {answers.get('problem', 'not specified')}. "
        f"The target users are {answers.get('users', 'not specified')}. "
        f"Here is what a user does in the app: {answers.get('core_loop', 'not specified')}. "
        f"The MVP is: {answers.get('mvp', 'not specified')}. "
        f"The tech stack is: {answers.get('stack', 'not specified')}. "
        f"Technical requirements include: {answers.get('technical', 'not specified')}. "
        f"The riskiest part is: {answers.get('risks', 'not specified')}. "
        f"I can cut: {answers.get('cuts', 'not specified')} if needed. "
        f"Done means: {answers.get('done', 'not specified')}."
    )


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


def generate_plan(project_paragraph, bot, llm_client):
    """
    Generates the full project plan in two steps:
    1. One retrieval pass — finds the most relevant docs for the whole project
    2. One LLM call — project paragraph + retrieved docs → full structured plan
    """
    logger.info("Starting plan generation")
    print("\nGenerating your plan...\n")

    # Step 1: retrieve top 5 docs using the project paragraph as the query
    print("  [1/2] Retrieving relevant documentation...")
    snippets = bot.retrieve(project_paragraph, top_k=5)
    logger.info("Retrieved %d docs: %s", len(snippets), [f for f, _ in snippets])

    # Step 2: one LLM call generates the entire plan
    print("  [2/2] Generating your plan...\n")
    plan = llm_client.generate_full_plan(project_paragraph, snippets)

    logger.info("Plan generation complete")
    return plan


def run_planner(bot, llm_client):
    """
    Main entry point for the planner mode. Called from main.py.
    """
    if llm_client is None:
        print("\nThe planner requires a Gemini API key. Please set GEMINI_API_KEY in your .env file.\n")
        return

    # Stage 1: planning conversation
    answers = ask_planning_questions()

    if not show_summary_and_confirm(answers):
        print("\nNo problem — come back when you're ready.\n")
        return

    # Stage 2: assemble paragraph and generate plan
    project_paragraph = assemble_paragraph(answers)
    plan = generate_plan(project_paragraph, bot, llm_client)

    print("=" * 60)
    print("YOUR PROJECT PLAN")
    print("=" * 60)
    print()
    print(plan)
    print()
