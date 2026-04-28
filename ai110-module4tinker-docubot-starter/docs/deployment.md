# Deployment

## Overview
Deployment is the process of making your application available to real users. A good deployment process is repeatable, automated, and keeps production stable. Start simple and add complexity only when needed.

## Deployment Checklist
Before deploying any application:
- [ ] All environment variables are set in the hosting platform (not in code)
- [ ] Debug mode is off in production
- [ ] Dependencies are pinned in `requirements.txt`
- [ ] Database migrations are applied
- [ ] `.env` is in `.gitignore`
- [ ] Secrets are not in version control
- [ ] Application starts without errors locally
- [ ] Basic error handling is in place
- [ ] Logging is configured

## requirements.txt
Pin your dependencies so the same versions install everywhere:
```bash
pip freeze > requirements.txt
```

Example output:
```
flask==3.0.0
sqlalchemy==2.0.23
python-dotenv==1.0.0
google-genai==1.0.0
bcrypt==4.1.2
```

## Simple Deployment Platforms
For new projects, start with a platform-as-a-service (PaaS) — they handle servers, networking, and scaling for you.

**Recommended for beginners:**
- **Railway** — simple, free tier, supports PostgreSQL
- **Render** — free tier, easy GitHub integration
- **Heroku** — industry standard, well-documented

**General deployment steps (Railway/Render):**
1. Push code to GitHub
2. Connect your GitHub repo to the platform
3. Set environment variables in the platform dashboard
4. Deploy — the platform installs dependencies and starts your app

## Environment Parity
Production should mirror development as closely as possible:
- Use PostgreSQL in both development and production (not SQLite in dev, PostgreSQL in prod)
- Use the same Python version
- Use the same dependency versions

Differences between dev and prod environments are a common source of bugs that only appear after deployment.

## Running the Application
```bash
# Development
python main.py

# Production (with gunicorn for Python web apps)
pip install gunicorn
gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT
```

## Health Checks
Add a health check endpoint so your platform knows if the app is running:
```python
@app.route("/health")
def health():
    return {"status": "ok"}, 200
```

## Database in Production
- Never run migrations manually in production without a rollback plan
- Always back up the database before running migrations
- Test migrations on staging first

## Logs in Production
Your hosting platform will capture stdout/stderr. Make sure:
- You log to stdout (not just to a file)
- Log level is INFO or WARNING (not DEBUG — too noisy)
- Errors include enough context to diagnose without a debugger

## Common Deployment Mistakes
- Forgetting to set environment variables in production
- Leaving debug mode on (exposes stack traces to users)
- Not pinning dependencies (works locally, breaks in production)
- Skipping database migrations after schema changes
- Deploying directly to production without testing on staging first
- No health check endpoint
