# Testing

## Overview
Tests verify that your code does what you expect and catch regressions when you make changes. A project without tests is hard to maintain and dangerous to change. Write tests as you build, not after.

## Types of Tests

**Unit tests** — test a single function in isolation
- Fast to run
- No database, no network
- Test one thing at a time

**Integration tests** — test how components work together
- May hit a test database
- Test a full request/response cycle
- Slower but catch more real bugs

**End-to-end tests** — test the full system from user input to output
- Slowest
- Catch issues unit tests miss
- Use sparingly for critical user flows

**Start with unit tests and integration tests. Add end-to-end tests for critical paths only.**

## Writing Good Tests
Each test should:
1. Set up the data it needs (Arrange)
2. Call the function being tested (Act)
3. Check the result (Assert)

```python
# Unit test example (pytest)
def test_generate_token_returns_string():
    token = generate_token(user_id=42)
    assert isinstance(token, str)
    assert len(token) > 0

def test_verify_token_returns_user_id():
    token = generate_token(user_id=42)
    payload = verify_token(token)
    assert payload["user_id"] == 42
```

## Test Naming
Name tests after what they verify:
- `test_login_with_valid_credentials_returns_token`
- `test_login_with_wrong_password_returns_401`
- `test_create_user_with_duplicate_email_returns_409`

Readable test names make failures self-explanatory.

## What to Test
- Happy path: the normal, successful case
- Edge cases: empty input, zero, maximum values
- Error cases: invalid input, missing fields, unauthorized access
- Boundaries: what happens at the limit of valid input

## What Not to Test
- Third-party library behavior (they have their own tests)
- Implementation details that are likely to change
- Private methods directly (test through the public interface)

## Running Tests with pytest
```bash
pip install pytest
pytest                          # Run all tests
pytest tests/test-auth.py       # Run a specific file
pytest -v                       # Verbose output
pytest -k "test_login"          # Run tests matching a name pattern
```

## Test File Structure
```
tests/
├── test-auth.py
├── test-user-model.py
├── test-api-users.py
└── conftest.py         # Shared fixtures and setup
```

## Fixtures
Use fixtures to set up shared test data:
```python
import pytest

@pytest.fixture
def test_user():
    return {"email": "test@example.com", "password": "testpassword"}

def test_login(test_user):
    response = client.post("/auth/login", json=test_user)
    assert response.status_code == 200
```

## Test Coverage
Aim for high coverage on business logic and API endpoints. Coverage measures which lines of code are executed by tests.

```bash
pip install pytest-cov
pytest --cov=src --cov-report=term-missing
```

## Common Testing Mistakes
- Writing tests after the project is complete (too painful, often skipped)
- Only testing the happy path
- Tests that depend on each other or on order of execution
- Not cleaning up test data between tests
- Mocking too much — tests that pass but hide real bugs
