# Authentication and Authorization

## Overview
Authentication verifies who a user is. Authorization determines what they are allowed to do. Both are required for any application that has user accounts or protected resources.

## Core Concepts
- **Authentication** — login, verify identity, issue a token or session
- **Authorization** — check permissions before allowing access to a resource
- **JWT (JSON Web Token)** — a signed token that proves identity without hitting the database on every request
- **Session** — server-side storage of login state, identified by a session ID in a cookie
- **Hashing** — one-way transformation of a password so it cannot be reversed if stolen

## Password Hashing
Never store plain text passwords. Always hash passwords before saving to the database.

```python
import bcrypt

# Hashing a password on registration
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# Verifying a password on login
is_valid = bcrypt.checkpw(password.encode(), hashed)
```

Use `bcrypt`, `argon2`, or `scrypt`. Never use MD5 or SHA-1 for passwords.

## JWT Authentication Flow
1. User submits username and password to `POST /auth/login`
2. Server verifies credentials against hashed password in database
3. Server generates a signed JWT containing user ID and expiry
4. Client stores the JWT (in memory or httpOnly cookie)
5. Client includes JWT in `Authorization: Bearer <token>` header on future requests
6. Server validates token signature and expiry on each protected request

```python
import jwt
import os

SECRET_KEY = os.getenv("AUTH_SECRET_KEY")

def generate_token(user_id):
    payload = {"user_id": user_id, "exp": datetime.utcnow() + timedelta(hours=24)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token):
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
```

## Protecting Routes with Middleware
Use middleware to protect routes instead of repeating auth checks in every handler.

```python
def require_auth(f):
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        try:
            user = verify_token(token)
            request.user = user
        except jwt.ExpiredSignatureError:
            return {"error": "Token expired"}, 401
        except jwt.InvalidTokenError:
            return {"error": "Invalid token"}, 401
        return f(*args, **kwargs)
    return wrapper
```

## Environment Variables for Auth
Never hardcode secret keys. Store them in environment variables:
```
AUTH_SECRET_KEY=your-long-random-secret-here
TOKEN_LIFETIME_SECONDS=86400
```

## Common Auth Mistakes
- Storing passwords in plain text
- Hardcoding secret keys in source code
- Using short or predictable secret keys
- Not setting token expiry
- Storing JWTs in localStorage (vulnerable to XSS — prefer httpOnly cookies)
- Skipping authorization checks (checking login but not permissions)

## Role-Based Access Control (RBAC)
For apps with different user types (admin, user, guest):
- Store a `role` field on the user record
- Include role in the JWT payload
- Check role in middleware before allowing access to sensitive routes
