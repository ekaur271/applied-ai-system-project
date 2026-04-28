# Project Structure

## Overview
A well-organized project structure makes code easier to navigate, maintain, and scale. Every new project should define a clear folder layout before writing code.

## Recommended Folder Layout

```
my-project/
├── src/                  # All application source code
│   ├── routes/           # API route handlers
│   ├── models/           # Database models and schemas
│   ├── services/         # Business logic layer
│   ├── middleware/        # Auth, logging, error middleware
│   └── utils/            # Shared helper functions
├── tests/                # All test files mirror src/ structure
├── docs/                 # Project documentation
├── scripts/              # One-off scripts, migrations, seeds
├── .env.example          # Template for environment variables
├── .gitignore            # Files to exclude from version control
├── requirements.txt      # Python dependencies (or package.json for Node)
└── README.md             # Project overview and setup instructions
```

## Naming Conventions
- Use lowercase with hyphens for folders and files: `user-service.py`, not `UserService.py`
- Name files after what they do: `auth-middleware.py`, `user-model.py`
- Keep test files next to or mirroring the files they test: `tests/test-user-model.py`
- Constants and config files use uppercase: `DATABASE_URL`, `SECRET_KEY`

## Separation of Concerns
Each layer has one responsibility:
- **Routes** — receive HTTP requests, call services, return responses. No business logic here.
- **Services** — contain business logic. No direct database calls, no HTTP concepts.
- **Models** — define data shape and database interaction only.
- **Utils** — pure helper functions with no side effects.

## What Not to Do
- Do not put all code in one file. Split by responsibility as soon as a file exceeds ~200 lines.
- Do not mix business logic into route handlers.
- Do not hardcode configuration values. Use environment variables.
- Do not commit generated files, secrets, or large binaries.

## Starting a New Project
1. Create the folder structure before writing any logic.
2. Initialize version control immediately: `git init`
3. Create `.gitignore` before your first commit.
4. Write a basic README before inviting collaborators.
5. Add `.env.example` to document required environment variables.
