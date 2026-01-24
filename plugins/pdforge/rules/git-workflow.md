# Git Workflow Rules

Git 操作的约束和规范。所有涉及 Git 操作的 Agent 必须遵守。

## Branch Naming Convention

### Format
```
<type>/<ticket-id>-<short-description>
```

### Types
| Type | Purpose | Example |
|------|---------|---------|
| feature | New functionality | `feature/AUTH-123-user-login` |
| fix | Bug fixes | `fix/BUG-456-null-pointer` |
| hotfix | Urgent production fixes | `hotfix/PROD-789-payment-crash` |
| refactor | Code improvement | `refactor/TECH-101-extract-service` |
| docs | Documentation only | `docs/DOC-202-api-reference` |
| test | Test additions/fixes | `test/TEST-303-integration-tests` |
| chore | Maintenance tasks | `chore/CHORE-404-upgrade-deps` |

### Rules
- All lowercase
- Hyphens for spaces (no underscores)
- Max 50 characters for description
- Include ticket ID when available

```bash
# ✅ Good
feature/AUTH-123-oauth-google
fix/BUG-456-session-timeout
hotfix/critical-payment-fix

# ❌ Bad
Feature/Auth_google          # Wrong case, underscore
my-branch                    # No type prefix
feature/implementing-the-new-user-authentication-flow  # Too long
```

## Commit Message Format

### Structure
```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### Types
| Type | When to use |
|------|-------------|
| feat | New feature |
| fix | Bug fix |
| docs | Documentation changes |
| style | Formatting, no code change |
| refactor | Code change, no feature/fix |
| perf | Performance improvement |
| test | Adding/fixing tests |
| chore | Maintenance, dependencies |
| ci | CI/CD changes |
| revert | Reverting changes |

### Rules
- Subject: imperative mood, max 50 chars, no period
- Body: wrap at 72 chars, explain what and why
- Footer: reference issues, breaking changes

```bash
# ✅ Good
feat(auth): add Google OAuth login
fix(api): handle null user in response
docs(readme): update installation steps

# With body
feat(payments): implement Stripe checkout

Add Stripe integration for one-time payments.
Includes webhook handling for payment confirmation.

Closes #123

# ❌ Bad
Added stuff                  # Vague, no type
feat: Add Google OAuth login. # Period at end
FEAT(AUTH): ADD LOGIN        # Caps
```

## Branch Workflow

### Main Branches
```
main (or master)     ← Production-ready code
  └── develop        ← Integration branch (optional)
        └── feature/* ← Feature branches
```

### Rules
1. **Never commit directly to main**
   - All changes via PR/merge
   - Exception: hotfixes with immediate review

2. **Keep branches short-lived**
   - Target: < 1 week
   - Large features: break into smaller PRs

3. **Rebase before merge**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

4. **Delete after merge**
   ```bash
   git branch -d feature/xyz
   git push origin --delete feature/xyz
   ```

## Pull Request Rules

### Title Format
```
[TYPE] Short description (#ticket)
```

Example: `[FEAT] Add user authentication (#AUTH-123)`

### PR Checklist
- [ ] Tests pass
- [ ] Coverage maintained or improved
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Reviewed by at least 1 person (for production)

### Size Guidelines
| Size | Lines Changed | Review Time |
|------|---------------|-------------|
| XS | < 50 | < 30 min |
| S | 50-200 | < 1 hour |
| M | 200-500 | < 2 hours |
| L | 500-1000 | Split if possible |
| XL | > 1000 | Must split |

## Merge Strategy

### Default: Squash Merge
```bash
git merge --squash feature/xyz
git commit -m "feat(scope): description (#PR)"
```

**When to use**: Most PRs, keeps history clean

### Merge Commit
```bash
git merge --no-ff feature/xyz
```

**When to use**: Large features where individual commits matter

### Rebase Merge
```bash
git rebase main feature/xyz
git checkout main
git merge feature/xyz
```

**When to use**: Linear history preference

## Protected Branch Rules

### main/master
- Require PR reviews: 1 (production: 2)
- Require status checks: all CI must pass
- Require up-to-date branches
- No force push
- No deletion

### develop (if used)
- Require PR reviews: 1
- Require status checks: CI must pass
- Allow rebase merge

## Git Hooks (Recommended)

### pre-commit
```bash
#!/bin/bash
# Run linter
npm run lint --fix
git add -A

# Run type check
npm run typecheck
```

### commit-msg
```bash
#!/bin/bash
# Validate commit message format
commit_regex='^(feat|fix|docs|style|refactor|perf|test|chore|ci|revert)(\(.+\))?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "Invalid commit message format"
    exit 1
fi
```

### pre-push
```bash
#!/bin/bash
# Run tests before push
npm test
```

## Emergency Procedures

### Hotfix Process
1. Branch from main: `git checkout -b hotfix/critical-fix main`
2. Fix and test locally
3. Get expedited review (Slack/call reviewer)
4. Merge to main
5. Cherry-pick to develop (if exists)
6. Deploy immediately

### Rollback Process
```bash
# Revert specific commit
git revert <commit-sha>
git push origin main

# Reset to known good state (destructive)
git reset --hard <good-commit-sha>
git push origin main --force  # Requires admin
```

## Verification Commands

```bash
# Check branch naming
git branch --list | grep -vE "^[*]?\s*(main|master|develop|feature/|fix/|hotfix/)"

# Validate recent commits
git log --oneline -10 | grep -vE "^[a-f0-9]+ (feat|fix|docs|style|refactor|perf|test|chore|ci|revert)"

# Find large PRs (> 500 lines)
git diff --stat main...HEAD | tail -1
```

## References

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
