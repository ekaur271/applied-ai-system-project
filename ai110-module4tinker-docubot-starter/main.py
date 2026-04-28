from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("docubot.log")
    ]
)

from docubot import DocuBot
from llm_client import GeminiClient
from dataset import SAMPLE_QUERIES
from planner import run_planner


def try_create_llm_client():
    try:
        client = GeminiClient()
        return client, True
    except RuntimeError as e:
        print(f"Warning: LLM features disabled. {e}\n")
        return None, False


def choose_mode(has_llm):
    print("\nChoose a mode:")
    print(f"  1) Naive LLM {'(no retrieval)' if has_llm else '(unavailable — no API key)'}")
    print("  2) Retrieval only (no LLM)")
    print(f"  3) RAG {'(retrieval + LLM)' if has_llm else '(unavailable — no API key)'}")
    print(f"  4) Project Planner {'(plan a new coding project)' if has_llm else '(unavailable — no API key)'}")
    print("  q) Quit")
    return input("\nEnter choice: ").strip().lower()


def get_query_or_use_samples():
    print("\nPress Enter to run sample queries, or type a custom query.")
    custom = input("Query: ").strip()
    return ([custom], "custom query") if custom else (SAMPLE_QUERIES, "sample queries")


def run_naive_llm_mode(bot, has_llm):
    if not has_llm:
        print("\nNaive LLM mode requires a GEMINI_API_KEY.\n")
        return
    queries, label = get_query_or_use_samples()
    print(f"\nRunning naive LLM mode on {label}...\n")
    all_text = bot.full_corpus_text()
    for query in queries:
        print("=" * 60)
        print(f"Question: {query}\n")
        print(bot.llm_client.naive_answer_over_full_docs(query, all_text))
        print()


def run_retrieval_only_mode(bot):
    queries, label = get_query_or_use_samples()
    print(f"\nRunning retrieval only mode on {label}...\n")
    for query in queries:
        print("=" * 60)
        print(f"Question: {query}\n")
        print(bot.answer_retrieval_only(query))
        print()


def run_rag_mode(bot, has_llm):
    if not has_llm:
        print("\nRAG mode requires a GEMINI_API_KEY.\n")
        return
    queries, label = get_query_or_use_samples()
    print(f"\nRunning RAG mode on {label}...\n")
    for query in queries:
        print("=" * 60)
        print(f"Question: {query}\n")
        print(bot.answer_rag(query))
        print()


def main():
    print("SWE Mentor")
    print("=" * 60)

    llm_client, has_llm = try_create_llm_client()
    bot = DocuBot(llm_client=llm_client)

    while True:
        choice = choose_mode(has_llm)
        if choice == "q":
            print("\nGoodbye.")
            break
        elif choice == "1":
            run_naive_llm_mode(bot, has_llm)
        elif choice == "2":
            run_retrieval_only_mode(bot)
        elif choice == "3":
            run_rag_mode(bot, has_llm)
        elif choice == "4":
            run_planner(bot, llm_client)
        else:
            print("\nInvalid choice. Enter 1, 2, 3, 4, or q.\n")


if __name__ == "__main__":
    main()
