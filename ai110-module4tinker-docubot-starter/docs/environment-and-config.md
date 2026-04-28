# Environment Variables and Configuration

## Overview
Configuration values like API keys, database URLs, and secret keys must never be hardcoded in source code. Use environment variables to keep secrets out of your codebase and to make your application behave differently across environments (development, staging, production).

## Why Environment Variables
- Secrets stay out of version control and off GitHub
- Different environments (dev, prod) can have different values without code changes
- Easy to rotate keys without changing code
- Required by most cloud deployment platforms

## The .env File
Store environment variables in a `.env` file during development:
```
GEMINI_API_KEY=your-api-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/mydb
AUTH_SECRET_KEY=a-long-random-string-here
DEBUG=true
PORT=8000
```

**Critical rules:**
- Add `.env` to `.gitignore` immediately — never commit it
- Create `.env.example` with placeholder values and commit that instead
- Never share your `.env` file with anyone

## .env.example Template
```
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
AUTH_SECRET_KEY=replace_with_long_random_secret
DEBUG=false
PORT=8000
```

This documents what variables are required without exposing real values.

## Loading Environment Variables in Python
```python
# Install: pip install python-dotenv
from dotenv import load_dotenv
import os

load_dotenv()  # Loads .env file into environment

api_key = os.getenv("GEMINI_API_KEY")
database_url = os.getenv("DATABASE_URL")
debug = os.getenv("DEBUG", "false").lower() == "true"
port = int(os.getenv("PORT", "8000"))
```

## Failing Fast on Missing Config
Validate required variables at startup, not mid-request:
```python
def load_config():
    required = ["GEMINI_API_KEY", "DATABASE_URL", "AUTH_SECRET_KEY"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
```

This fails immediately with a clear message rather than failing silently later.

## Environments
**Development** — local machine, debug mode on, SQLite or local PostgreSQL
**Staging** — cloud server, mirrors production, used for testing before release
**Production** — live server, debug off, real database, real API keys

Use different `.env` values per environment. Never use production API keys in development.

## Secrets Management in Production
In production, do not use `.env` files. Instead:
- Set environment variables directly in your hosting platform (Heroku, Railway, Render, AWS)
- Use a secrets manager (AWS Secrets Manager, HashiCorp Vault) for sensitive keys
- Never pass secrets through command-line arguments (visible in process list)

## Common Configuration Mistakes
- Committing `.env` to GitHub (happens constantly — use a pre-commit hook or GitHub secret scanning)
- Hardcoding API keys or passwords directly in code
- Using the same secret key across all environments
- Not documenting required variables in `.env.example`
- Reading environment variables inside functions (read at startup instead)
