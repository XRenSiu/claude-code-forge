---
description: Auto commit all changes and push to remote
---

# Auto Commit and Push

Automatically stage all changes, create a commit with AI-generated message, and push to remote.

## Parameters

- `$ARGUMENTS`: Custom commit message (optional). If not provided, generate based on changes.

## Instructions

1. **Check for changes**:
   - Run `git status` to see if there are any changes
   - If no changes (working tree clean), inform user and stop

2. **Get current branch**:
   - Run `git branch --show-current` to get current branch name
   - Check if branch has upstream with `git rev-parse --abbrev-ref @{upstream}`

3. **Analyze changes**:
   - Run `git diff` and `git diff --staged` to see all changes
   - Run `git status --porcelain` to see untracked files

4. **Generate commit message**:
   - If `$ARGUMENTS` is provided, use it as the commit message
   - Otherwise, analyze the changes and generate a concise commit message following conventional commits format:
     - `feat:` for new features
     - `fix:` for bug fixes
     - `refactor:` for refactoring
     - `docs:` for documentation
     - `style:` for formatting changes
     - `test:` for tests
     - `chore:` for maintenance tasks

5. **Stage and commit**:
   ```bash
   git add -A
   git commit -m "${COMMIT_MESSAGE}

   Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

6. **Push to remote**:
   - If upstream exists: `git push`
   - If no upstream: `git push -u origin ${BRANCH_NAME}`

7. **Report results**:
   - Show the commit hash and message
   - Show push result
   - If any step fails, show error and stop

## Error Handling

- If `git add` fails, show error
- If `git commit` fails (e.g., pre-commit hook), show the error and attempt to fix if files were auto-modified
- If `git push` fails, show error and suggest `git pull --rebase` if needed
