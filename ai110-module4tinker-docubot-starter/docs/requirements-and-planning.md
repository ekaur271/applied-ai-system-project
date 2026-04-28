# Requirements and Planning

## Overview
Planning before coding prevents wasted effort. Every project should start with a clear problem statement, a scoped MVP, and a breakdown of features into tasks before writing a single line of code.

## Define the Problem
Start by answering three questions:
1. What problem does this solve?
2. Who is the user?
3. What does success look like?

Write these down in one paragraph before anything else. If you cannot answer all three, you are not ready to plan features.

## Writing User Stories
User stories describe features from the user's perspective. Format:
> As a [user type], I want to [do something] so that [I get some benefit].

Examples:
- As a user, I want to create an account so that I can save my data.
- As an admin, I want to view all users so that I can manage access.
- As a developer, I want clear error messages so that I can debug quickly.

User stories keep features grounded in real needs and prevent over-engineering.

## Scoping an MVP
An MVP (Minimum Viable Product) is the smallest version of your project that demonstrates its core value. Cut everything that is not essential to the core use case.

**Keep in MVP:**
- Core user flow end to end
- Basic authentication if users need accounts
- One working version of each major feature

**Cut from MVP:**
- Nice-to-have UI polish
- Advanced filtering or search
- Admin dashboards
- Third-party integrations

## Breaking Down Features into Tasks
Once you have user stories, break each into concrete tasks:
1. Design database schema
2. Create API endpoint
3. Write service logic
4. Add input validation
5. Write tests
6. Update documentation

Each task should be completable in a few hours. If a task takes longer, break it down further.

## Prioritization
Order tasks by dependency. Build the foundation first:
1. Project structure and environment setup
2. Database schema and models
3. Authentication
4. Core API endpoints
5. Business logic
6. Frontend or CLI
7. Testing and error handling
8. Documentation and deployment

## Common Planning Mistakes
- Building features before the data model is stable
- Skipping authentication planning until the end
- Underestimating time for testing and debugging
- Adding features mid-project without re-scoping the MVP
