# Documentation

## Overview
Documentation explains what your code does, how to use it, and why decisions were made. Good documentation makes your project usable by others and by your future self. Write the minimum necessary — but write it well.

## The README
Every project must have a README. It is the first thing anyone sees on GitHub. A good README answers:
1. What does this project do?
2. How do I set it up?
3. How do I use it?
4. What are the known limitations?

**README structure:**
```markdown
# Project Name
One paragraph describing what it does and who it is for.

## Setup
Step-by-step instructions to install and run the project.

## Usage
How to use the project with concrete examples.

## Configuration
What environment variables are required and what they do.

## Contributing
How others can contribute (optional for solo projects).
```

## .env.example
Document all required environment variables in `.env.example`. Every variable should have a comment explaining what it is and where to get it:

```
# Get your API key from https://aistudio.google.com
GEMINI_API_KEY=your_api_key_here

# PostgreSQL connection string
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Long random string used to sign JWT tokens
AUTH_SECRET_KEY=replace_with_long_random_secret
```

## Inline Comments
Write comments only when the WHY is not obvious from the code itself.

```python
# Good comment — explains a non-obvious constraint
# bcrypt has a 72-byte input limit; truncate before hashing
password = password[:72]

# Bad comment — just restates what the code does
# Hash the password
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# Bad comment — references the task or PR
# Added for the auth flow (issue #42)
```

Delete commented-out code before merging. Use version control to recover old code.

## Docstrings
Write docstrings for public functions and classes that are part of an API or library. Keep them short.

```python
def retrieve(query, top_k=3):
    """Return the top_k most relevant documents for the given query."""
    ...

class DocuBot:
    """Documentation assistant that answers questions using RAG."""
    ...
```

Do not write multi-paragraph docstrings for internal helper functions. The function name and type hints should be enough.

## API Documentation
For REST APIs, document each endpoint:
- Method and URL
- Required and optional parameters
- Request body format
- Response format and status codes
- Authentication requirements
- Example request and response

Tools like Swagger/OpenAPI can auto-generate this from code annotations.

## Changelog
For projects with users or collaborators, maintain a CHANGELOG.md that records what changed between versions:

```markdown
## [1.2.0] - 2024-01-15
### Added
- RAG mode with retrieval from local docs folder

### Fixed
- Empty query now returns a clear error message instead of crashing
```

## What Not to Document
- Implementation details that are clear from well-named code
- Every parameter of an internal function
- Things that change frequently (keep docs close to the code that changes)

The best documentation is code that is so clear it barely needs explaining.

## Documentation Checklist
- [ ] README explains what the project does and how to run it
- [ ] .env.example lists all required environment variables with descriptions
- [ ] Setup instructions work on a fresh machine
- [ ] Sample inputs and outputs are shown
- [ ] Non-obvious code decisions have inline comments
- [ ] Public functions have docstrings
