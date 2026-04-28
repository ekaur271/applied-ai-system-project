# Error Handling and Logging

## Overview
Error handling prevents crashes from becoming user-facing failures. Logging records what your system is doing so you can debug problems after they happen. Both are required in any production-quality application.

## Error Handling Principles
- Never let unexpected errors crash the program silently
- Return clear, actionable error messages to the user
- Log the full error internally, show a safe message externally
- Handle errors at the right level — not too early, not too late

## Python Error Handling
```python
try:
    result = do_something_risky()
except ValueError as e:
    # Handle a specific, expected error
    logger.warning(f"Invalid input: {e}")
    return {"error": "Invalid input provided"}, 400
except Exception as e:
    # Catch unexpected errors — log fully, return generic message
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return {"error": "Something went wrong. Please try again."}, 500
```

## What to Handle vs What to Let Raise
**Handle explicitly:**
- Invalid user input (bad format, missing fields)
- Resource not found (user, record)
- Authentication failures (bad token, expired token)
- External API failures (network timeout, bad response)

**Let raise (or catch at top level):**
- Programming errors (AttributeError, TypeError) — these are bugs, fix them
- Missing environment variables — fail fast at startup, not mid-request

## Logging Setup
Use Python's built-in `logging` module. Never use `print()` for application events.

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),                        # Console output
        logging.FileHandler("app.log")                  # File output
    ]
)

logger = logging.getLogger(__name__)
```

## Log Levels
Use the right level for each event:

| Level | Use for |
|-------|---------|
| `DEBUG` | Detailed diagnostic info during development |
| `INFO` | Normal application events (startup, request received) |
| `WARNING` | Something unexpected but handled (retried, fell back) |
| `ERROR` | Something failed that needs attention |
| `CRITICAL` | System is broken, cannot continue |

```python
logger.debug("Processing query: %s", query)
logger.info("User %s logged in", user_id)
logger.warning("Retrieval returned 0 results for query: %s", query)
logger.error("Database connection failed: %s", str(e), exc_info=True)
```

## What to Log
**Always log:**
- Application startup and configuration
- Incoming requests (method, path, user ID)
- Errors and exceptions with stack traces
- External API calls and their outcomes
- Important state changes (user created, payment processed)

**Never log:**
- Passwords, tokens, or API keys
- Full request bodies that may contain sensitive data
- High-volume events that create noise (every DB query in prod)

## Guardrails
Guardrails are checks that prevent bad state from propagating through the system:

```python
def retrieve(query, top_k=3):
    if not query or not query.strip():
        logger.warning("Empty query received, returning no results")
        return []
    if len(query) > 1000:
        logger.warning("Query too long (%d chars), truncating", len(query))
        query = query[:1000]
    # proceed with retrieval
```

## Global Error Handler (Flask example)
Catch unhandled exceptions at the application level:
```python
@app.errorhandler(Exception)
def handle_unexpected_error(e):
    logger.error("Unhandled exception: %s", str(e), exc_info=True)
    return {"error": "An unexpected error occurred"}, 500
```

## Common Mistakes
- Using `print()` instead of `logging`
- Catching `Exception` everywhere and swallowing errors silently
- Logging sensitive data (tokens, passwords)
- No logging at all until something breaks in production
- Returning internal error details to users (stack traces, SQL errors)
