# Design Patterns

## Overview
Design patterns are proven solutions to common software problems. You do not need to memorize all of them. Learn the ones that appear most often in web and backend development and apply them when the problem fits — not everywhere.

## MVC (Model-View-Controller)
MVC separates an application into three layers:
- **Model** — data and business rules
- **View** — what the user sees (HTML, JSON response)
- **Controller** — receives input, calls the model, returns the view

In a REST API, routes are controllers, services are models, and JSON responses are views.

```
Request → Route Handler (Controller)
              → Service Layer (Model/Business Logic)
                   → Database Model
              → JSON Response (View)
```

## Service Layer Pattern
Move business logic out of route handlers into a separate service layer.

```python
# Bad — business logic in the route handler
@app.route("/users", methods=["POST"])
def create_user():
    data = request.json
    hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt())
    user = User(email=data["email"], password_hash=hashed)
    db.add(user)
    db.commit()
    return user.to_dict(), 201

# Good — route delegates to a service
@app.route("/users", methods=["POST"])
def create_user():
    user = user_service.create(request.json)
    return user.to_dict(), 201

# In user_service.py
def create(data):
    validate_user_data(data)
    hashed = hash_password(data["password"])
    user = User(email=data["email"], password_hash=hashed)
    db.add(user)
    db.commit()
    return user
```

This makes the business logic testable independently of HTTP.

## Repository Pattern
Abstract database access behind a repository so you can swap the database or mock it in tests.

```python
class UserRepository:
    def find_by_id(self, user_id):
        return db.query(User).filter(User.id == user_id).first()

    def find_by_email(self, email):
        return db.query(User).filter(User.email == email).first()

    def save(self, user):
        db.add(user)
        db.commit()
        return user
```

## Factory Pattern
Use factories to create objects with complex setup:
```python
def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or "config.DefaultConfig")
    db.init_app(app)
    register_routes(app)
    return app
```

This is the standard Flask application factory pattern.

## Middleware / Decorator Pattern
Use decorators to add cross-cutting concerns (auth, logging, validation) without repeating code:
```python
def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = get_token_from_header()
        if not verify_token(token):
            return {"error": "Unauthorized"}, 401
        return f(*args, **kwargs)
    return wrapper

@app.route("/api/users")
@require_auth
def get_users():
    ...
```

## Singleton Pattern
Use for resources that should only be created once — like database connections or logging configuration:
```python
# Module-level initialization creates a single instance
engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(bind=engine)
```

## Strategy Pattern
Allow behavior to be swapped at runtime:
```python
class DocuBot:
    def __init__(self, retrieval_strategy):
        self.retriever = retrieval_strategy

    def answer(self, query):
        snippets = self.retriever.retrieve(query)
        return self.generate(snippets)
```

This is how DocuBot supports multiple retrieval strategies without changing its core logic.

## When Not to Use Patterns
- Do not apply a pattern just because you know it
- Premature abstraction makes code harder to read
- Start simple — add patterns when the code becomes painful to change
- Three similar functions is better than a premature abstraction
