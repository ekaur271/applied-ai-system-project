# Scalability

## Overview
Scalability is the ability of your system to handle more load without degrading in performance. Design for scalability from the start, but do not over-engineer before you have a real problem. Measure first, then optimize.

## Stateless Design
Make your application stateless — each request should contain everything the server needs to process it. Do not store session state in memory on the server.

**Why:** Stateless servers can be scaled horizontally (add more servers). Stateful servers cannot because the next request might hit a different server with no memory of the previous one.

**How:** Use JWTs instead of server-side sessions. Store state in the database or a cache like Redis.

## Pagination
Never return all records from a database query. Paginate all list endpoints.

```python
# Bad — returns all users
users = db.query(User).all()

# Good — paginate
def get_users(page=1, limit=20):
    offset = (page - 1) * limit
    return db.query(User).offset(offset).limit(limit).all()
```

Always include total count and pagination metadata in the response so clients know how many pages exist.

## Caching
Cache expensive or frequently repeated operations. Do not hit the database for the same data on every request.

**Types of caching:**
- **In-memory cache** — store results in a Python dict for the lifetime of the process (simple, not shared across servers)
- **Redis** — shared cache across multiple servers, supports TTL (time to live)
- **HTTP caching** — use `Cache-Control` headers to let browsers and CDNs cache responses

```python
import functools

@functools.lru_cache(maxsize=128)
def get_user_by_id(user_id):
    return db.query(User).filter(User.id == user_id).first()
```

Cache reads, not writes. Cache things that are expensive to compute and change infrequently.

## Avoiding N+1 Queries
The N+1 query problem occurs when you query for a list and then query for related data for each item.

```python
# Bad — 1 query for projects, then N queries for each owner
projects = db.query(Project).all()
for project in projects:
    print(project.owner.email)  # New query for each project

# Good — join in one query
projects = db.query(Project).options(joinedload(Project.owner)).all()
```

Use eager loading (joins) when you know you will need related data.

## Database Indexing
Add indexes on columns used in WHERE, ORDER BY, and JOIN clauses.

```sql
-- Without index: full table scan on every login
SELECT * FROM users WHERE email = 'user@example.com';

-- Add index
CREATE INDEX idx_users_email ON users(email);
```

Check your slow query log in production to identify queries that need indexes.

## Asynchronous Processing
Move slow or non-critical work out of the request/response cycle:
- Sending emails
- Generating reports
- Processing uploads
- Calling external APIs

Use a task queue (Celery + Redis, or RQ) to process these in the background.

## Horizontal vs Vertical Scaling
- **Vertical scaling** — bigger server (more CPU, RAM). Simple but has limits and single point of failure.
- **Horizontal scaling** — more servers. Requires stateless design and a load balancer.

Start with vertical scaling. Move to horizontal when vertical is no longer sufficient.

## Common Scalability Mistakes
- Storing session state in memory (blocks horizontal scaling)
- Returning unbounded lists from API endpoints
- No database indexes on frequently queried columns
- Calling external APIs synchronously in request handlers
- Caching writes instead of reads
- Optimizing before measuring — fix real bottlenecks, not imagined ones
