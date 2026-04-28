# Security

## Overview
Security is not optional. Common vulnerabilities are well-known and preventable. Most security breaches exploit basic mistakes, not sophisticated attacks. Follow these practices from the start.

## SQL Injection
SQL injection happens when user input is included directly in a SQL query, letting attackers run arbitrary SQL.

```python
# Vulnerable — never do this
query = f"SELECT * FROM users WHERE email = '{user_input}'"

# Safe — use parameterized queries
query = "SELECT * FROM users WHERE email = ?"
db.execute(query, (user_input,))

# Safe with ORM — SQLAlchemy handles this automatically
user = db.query(User).filter(User.email == user_input).first()
```

Always use parameterized queries or an ORM. Never concatenate user input into SQL strings.

## Cross-Site Scripting (XSS)
XSS allows attackers to inject malicious scripts into pages viewed by other users.

**Prevention:**
- Escape all user-generated content before rendering in HTML
- Use a templating engine that auto-escapes (Jinja2 does this by default)
- Set `Content-Security-Policy` headers
- Never use `innerHTML` with user data in JavaScript

## Input Validation
Validate all input at the boundary of your system — in route handlers before passing data anywhere else.

```python
def validate_user_input(data):
    if not data.get("email"):
        raise ValueError("Email is required")
    if "@" not in data["email"]:
        raise ValueError("Invalid email format")
    if len(data.get("password", "")) < 8:
        raise ValueError("Password must be at least 8 characters")
```

Never trust client-supplied data. Validate type, format, length, and range.

## CORS (Cross-Origin Resource Sharing)
CORS controls which domains can make requests to your API.

```python
from flask_cors import CORS

# Allow only specific origins
CORS(app, origins=["https://yourfrontend.com"])

# Never do this in production
CORS(app, origins="*")  # Allows any domain
```

In development, CORS errors are common and annoying — but in production, configure it strictly.

## Rate Limiting
Prevent abuse and brute-force attacks by limiting how many requests a client can make.

```python
from flask_limiter import Limiter

limiter = Limiter(app, default_limits=["100 per hour"])

@app.route("/auth/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    ...
```

Always rate-limit authentication endpoints specifically.

## Secure Headers
Set security headers on all responses:
```python
@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

## HTTPS
Always use HTTPS in production. Never send credentials or tokens over HTTP. Most hosting platforms provide HTTPS automatically.

## Dependency Security
Keep dependencies updated. Vulnerabilities are regularly discovered in third-party packages.

```bash
pip install pip-audit
pip-audit                       # Scan for known vulnerabilities
```

## Secrets Management
- Never hardcode secrets in source code
- Never commit `.env` files
- Rotate API keys and secrets regularly
- Use different secrets for development and production

## Common Security Mistakes
- SQL queries built with string concatenation
- Storing plain text passwords
- Committing API keys to GitHub
- Trusting user input without validation
- Allowing CORS from any origin in production
- No rate limiting on login endpoints
- Using HTTP in production
- Outdated dependencies with known vulnerabilities
