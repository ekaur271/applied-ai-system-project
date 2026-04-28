import logging

logger = logging.getLogger(__name__)


def ask_for_project_description():
    print("\n" + "=" * 60)
    print("SWE Mentor — Project Planner")
    print("=" * 60)
    print("\nDescribe your project in a paragraph. Try to cover:")
    print("  • What problem it solves and who it's for")
    print("  • What a user actually does in the app")
    print("  • Your MVP — the smallest version that proves the idea works")
    print("  • Your tech stack (or say 'suggest one')")
    print("  • What done looks like to you\n")
    description = input("Your project: ").strip()
    return description if description else "No description provided."


def confirm(description):
    print("\n" + "=" * 60)
    print("Here's what you described:")
    print("=" * 60)
    print(description)
    print()
    return input("Ready to generate your plan? (yes / no): ").strip().lower() in ("yes", "y")


def generate_plan(description, bot, llm_client):
    logger.info("Starting plan generation")
    print("\nGenerating your plan...\n")

    print("  [1/3] Expanding query to technical terms...")
    expanded = llm_client.expand_query(description)
    print(f"         → {expanded}\n")

    print("  [2/3] Retrieving relevant documentation...")
    snippets = bot.retrieve(description, top_k=5)
    if snippets:
        print("         → Retrieved:")
        for fname, _ in snippets:
            print(f"           • {fname}")
    print()

    print("  [3/3] Building your plan...\n")
    plan = llm_client.generate_full_plan(description, snippets)

    logger.info("Plan generation complete")
    return plan


def run_planner(bot, llm_client):
    if llm_client is None:
        print("\nThe planner requires a GEMINI_API_KEY. Add it to your .env file.\n")
        return

    description = ask_for_project_description()

    if not confirm(description):
        print("\nCome back when you're ready.\n")
        return

    plan = generate_plan(description, bot, llm_client)

    print("=" * 60)
    print("YOUR PROJECT PLAN")
    print("=" * 60)
    print()
    print(plan)
    print()
