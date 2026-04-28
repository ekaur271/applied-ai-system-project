# Database Design

## Overview
The database is the foundation of most applications. A well-designed schema is easier to query, scale, and maintain. Design your schema before writing any application code.

## Choosing a Database
**SQL (PostgreSQL, SQLite, MySQL)**
- Best for structured data with clear relationships
- Use when data integrity and relationships matter
- PostgreSQL for production, SQLite for development and small projects

**NoSQL (MongoDB, Firebase)**
- Best for flexible or rapidly changing data shapes
- Use when documents vary significantly between records
- Harder to enforce data integrity

**Default recommendation:** Start with PostgreSQL. It handles most use cases well and is the industry standard for web applications.

## Schema Design Principles
- Every table needs a primary key (use auto-incrementing `id` or UUID)
- Use foreign keys to enforce relationships between tables
- Store timestamps on every table: `created_at`, `updated_at`
- Normalize data to avoid duplication — store each fact in one place
- Use appropriate data types (don't store numbers as strings)

## Common Tables

**Users table:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Relationships example:**
```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Migrations
Never manually edit a production database schema. Use migrations to track and apply schema changes.

```bash
# Example with Flask-Migrate or Alembic
alembic revision --autogenerate -m "add projects table"
alembic upgrade head
```

Always commit migration files to version control. Never delete old migration files.

## Using an ORM
An ORM (Object-Relational Mapper) lets you interact with the database using Python objects instead of raw SQL.

```python
# SQLAlchemy example
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    projects = relationship("Project", back_populates="owner")
```

## Connection Setup
Store database connection strings in environment variables. Never hardcode credentials.

```
DATABASE_URL=postgresql://user:password@localhost:5432/mydb
```

```python
import os
from sqlalchemy import create_engine

engine = create_engine(os.getenv("DATABASE_URL"))
```

## Indexing
Add indexes on columns you frequently filter or sort by:
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
```

## Common Database Mistakes
- No primary keys or using non-unique values as keys
- Storing comma-separated values in a single column instead of a join table
- Not using foreign keys (orphaned records accumulate)
- Hardcoding database credentials in source code
- Running raw user input in SQL queries (SQL injection risk)
- Forgetting to add indexes on foreign key columns
