# Version Control

## Overview
Version control tracks every change to your code, lets you collaborate safely, and lets you recover from mistakes. Git is the industry standard. Every project must use version control from day one.

## Essential Git Commands
```bash
git init                        # Initialize a new repo
git clone <url>                 # Copy an existing repo
git status                      # See what has changed
git add <file>                  # Stage a file for commit
git add .                       # Stage all changed files
git commit -m "message"         # Save a snapshot with a message
git push origin main            # Upload commits to remote
git pull origin main            # Download latest changes
git log --oneline               # View commit history
git diff                        # See unstaged changes
```

## Branching Strategy
Never commit directly to `main`. Use branches for every feature or fix.

```bash
git checkout -b feature/user-auth     # Create and switch to new branch
git checkout main                     # Switch back to main
git merge feature/user-auth           # Merge branch into main
git branch -d feature/user-auth       # Delete branch after merge
```

**Branch naming conventions:**
- `feature/short-description` — new functionality
- `fix/short-description` — bug fixes
- `chore/short-description` — maintenance, dependency updates

## Writing Good Commit Messages
A good commit message completes the sentence: "If applied, this commit will..."

**Good:**
- `Add JWT authentication middleware`
- `Fix user email validation bug`
- `Update README with setup instructions`

**Bad:**
- `fix`
- `stuff`
- `wip`
- `asdfgh`

Keep the first line under 72 characters. If more context is needed, add a blank line and a longer description below.

## Pull Requests
When working with a team or on GitHub:
1. Push your branch to remote
2. Open a Pull Request (PR) against `main`
3. Describe what changed and why
4. Request a review
5. Merge only after approval

Even on solo projects, PRs create a record of what changed and why.

## .gitignore
Always create a `.gitignore` before your first commit. Common entries:

```
.env
__pycache__/
*.pyc
node_modules/
.DS_Store
venv/
*.log
dist/
build/
```

Never commit secrets, API keys, passwords, or large generated files.

## Recovering from Mistakes
```bash
git restore <file>              # Discard unstaged changes to a file
git reset HEAD <file>           # Unstage a file
git revert <commit-hash>        # Undo a commit without rewriting history
```

Never use `git reset --hard` on shared branches. It rewrites history and causes conflicts for collaborators.
