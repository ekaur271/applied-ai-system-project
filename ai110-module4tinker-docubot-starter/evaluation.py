from dataset import SAMPLE_QUERIES

EXPECTED_SOURCES = {
    "jwt": ["auth.md"],
    "authentication": ["auth.md"],
    "environment variables": ["environment-and-config.md"],
    "commit to github": ["version-control.md"],
    "project folders": ["project-structure.md"],
    "structure": ["project-structure.md"],
    "database": ["database.md"],
    "rest api": ["api-design.md"],
    "api endpoints": ["api-design.md"],
    "unit tests": ["testing.md"],
    "integration tests": ["testing.md"],
    "errors": ["error-handling-and-logging.md"],
    "exceptions": ["error-handling-and-logging.md"],
    "git": ["version-control.md"],
    "branching": ["version-control.md"],
    "scalable": ["scalability.md"],
    "security": ["security.md"],
    "vulnerabilities": ["security.md"],
    "deploy": ["deployment.md"],
    "production": ["deployment.md"],
    "design patterns": ["design-patterns.md"],
    "ai model": ["ai-integration.md"],
    "readme": ["documentation.md"],
    "mvp": ["requirements-and-planning.md"],
    "scope": ["requirements-and-planning.md"],
}


def expected_files_for_query(query):
    query_lower = query.lower()
    return [f for key, files in EXPECTED_SOURCES.items() if key in query_lower for f in files]


def evaluate_retrieval(bot, top_k=3):
    results = []
    hits = 0

    for query in SAMPLE_QUERIES:
        expected = expected_files_for_query(query)
        retrieved = bot.retrieve(query, top_k=top_k)
        retrieved_files = [fname for fname, _ in retrieved]
        hit = any(f in retrieved_files for f in expected) if expected else False
        if hit:
            hits += 1
        results.append({
            "query": query,
            "expected": expected,
            "retrieved": retrieved_files,
            "hit": hit
        })

    return hits / len(SAMPLE_QUERIES), results


def print_eval_results(hit_rate, results):
    print("\nEvaluation Results")
    print("-" * 40)
    print(f"Hit rate: {hit_rate:.2f}\n")
    for item in results:
        print(f"Query: {item['query']}")
        print(f"  Expected:  {item['expected']}")
        print(f"  Retrieved: {item['retrieved']}")
        print(f"  Hit:       {item['hit']}")
        print()


if __name__ == "__main__":
    from docubot import DocuBot

    print("Running retrieval evaluation...\n")
    bot = DocuBot()
    hit_rate, results = evaluate_retrieval(bot)
    print_eval_results(hit_rate, results)
