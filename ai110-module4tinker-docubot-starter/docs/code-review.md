# Code Review

## Overview
Code review is the practice of having another person (or yourself, after a break) read and evaluate your code before it is merged. It catches bugs, improves quality, and spreads knowledge across the team. Even on solo projects, reviewing your own PRs before merging is valuable.

## What Code Review Catches
- Logic bugs that tests missed
- Security vulnerabilities (unvalidated input, exposed secrets)
- Missing error handling
- Confusing naming or structure
- Duplicate code that should be a shared function
- Missing tests for edge cases

## How to Request a Good Review
Before asking for review:
- Run your tests and make sure they pass
- Review your own diff first
- Write a clear PR description: what changed, why, how to test it
- Keep PRs small — under 400 lines of changed code if possible

A reviewer cannot give useful feedback on a 2,000-line PR.

## How to Give a Good Review
Focus on:
- **Correctness** — does the code do what it claims?
- **Security** — is user input validated? Are secrets handled correctly?
- **Readability** — can you understand what the code does without running it?
- **Edge cases** — what happens with empty input, invalid data, or failure?
- **Tests** — are the right things tested?

Be specific. Instead of "this is confusing," say "I'm not sure what `x` refers to here — could this be named `user_id`?"

## Code Review Checklist
- [ ] Does the code do what the PR description says?
- [ ] Are there tests for the new behavior?
- [ ] Is input validated before use?
- [ ] Are errors handled appropriately?
- [ ] Are there any hardcoded secrets or credentials?
- [ ] Is the naming clear and consistent?
- [ ] Is there anything duplicated that could be shared?
- [ ] Does the code follow the project's existing patterns?

## Common Red Flags
```python
# Red flag: no error handling
result = call_external_api(data)
return result["value"]

# Red flag: hardcoded secret
API_KEY = "sk-abc123"

# Red flag: user input directly in query
query = f"SELECT * FROM users WHERE name = '{name}'"

# Red flag: catching all exceptions silently
try:
    do_something()
except:
    pass

# Red flag: function doing too many things (name suggests multiple responsibilities)
def validate_and_save_and_email_user(data):
    ...
```

## Giving Feedback Constructively
- Use questions over statements: "Have you considered what happens if this is None?"
- Distinguish blocking issues from suggestions: prefix non-blocking feedback with "Nit:" or "Optional:"
- Acknowledge good work: if something is well-done, say so
- Focus on the code, not the person: "this function" not "you wrote"

## Reviewing Your Own Code
Before submitting for review:
1. Read the full diff as if someone else wrote it
2. Check every changed file for obvious mistakes
3. Run the tests
4. Delete commented-out code and debug prints
5. Check for any hardcoded values that should be config

## When to Request Changes vs Approve
**Request changes when:**
- There is a correctness bug
- There is a security issue
- The change will break something for other developers

**Approve with comments when:**
- The code is correct but could be improved
- Your suggestions are style preferences, not bugs

**Approve when:**
- The code is correct, tested, and readable
