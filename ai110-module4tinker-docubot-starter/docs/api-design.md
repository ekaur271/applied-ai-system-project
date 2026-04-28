# API Design

## Overview
A well-designed API is consistent, predictable, and easy to use. REST (Representational State Transfer) is the most common pattern for web APIs. Follow conventions so developers can use your API without reading every line of documentation.

## REST Conventions

**URL structure:**
- Use nouns, not verbs: `/users` not `/getUsers`
- Use plural nouns: `/projects` not `/project`
- Nest related resources: `/users/42/projects`
- Keep URLs lowercase with hyphens: `/project-tasks` not `/projectTasks`

**HTTP methods:**
| Method | Use | Example |
|--------|-----|---------|
| GET | Retrieve data | `GET /users` |
| POST | Create a new resource | `POST /users` |
| PUT | Replace a resource | `PUT /users/42` |
| PATCH | Update part of a resource | `PATCH /users/42` |
| DELETE | Remove a resource | `DELETE /users/42` |

## HTTP Status Codes
Always return the correct status code. Do not return 200 for errors.

| Code | Meaning | Use when |
|------|---------|----------|
| 200 | OK | Successful GET, PATCH, DELETE |
| 201 | Created | Successful POST |
| 400 | Bad Request | Invalid input, missing fields |
| 401 | Unauthorized | Not logged in |
| 403 | Forbidden | Logged in but not allowed |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Duplicate email, unique constraint |
| 422 | Unprocessable Entity | Validation failed |
| 500 | Internal Server Error | Unexpected server error |

## Request and Response Format
Use JSON consistently. Always include `Content-Type: application/json`.

**Request body (POST /users):**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Success response:**
```json
{
  "id": 42,
  "email": "user@example.com",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error response:**
```json
{
  "error": "Email already exists",
  "field": "email"
}
```

## Input Validation
Validate all input before processing. Never trust client data.
- Check required fields are present
- Check data types and formats (email format, date format)
- Check length limits
- Return 400 with a clear error message for invalid input

## API Versioning
Prefix routes with a version number so you can make breaking changes later:
```
/api/v1/users
/api/v1/projects
```

## Pagination
Never return all records for large collections. Use pagination:
```
GET /api/v1/users?page=1&limit=20
```

Response should include pagination metadata:
```json
{
  "data": [...],
  "page": 1,
  "limit": 20,
  "total": 150
}
```

## Authentication Headers
Protected endpoints expect a JWT in the Authorization header:
```
Authorization: Bearer <token>
```

## Common API Design Mistakes
- Using verbs in URLs (`/getUser`, `/createProject`)
- Returning 200 for errors
- Returning all database fields including sensitive ones (password_hash, internal IDs)
- No pagination on list endpoints
- Inconsistent naming (snake_case in some places, camelCase in others)
- No input validation
