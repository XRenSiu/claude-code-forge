# /learn Command

**独特功能！** Extract reusable patterns from the current session into Skills or Rules.

## Purpose

Traditional workflow: Problem solved → Knowledge lost
With `/learn`: Problem solved → Pattern extracted → Knowledge preserved

This command analyzes the current conversation to identify:
- Recurring patterns
- Novel solutions
- Best practices discovered
- Anti-patterns avoided

## Usage

```
/learn [output-type] [options]
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| output-type | No | auto | What to create: skill, rule, pattern, auto |

## Options

| Option | Description |
|--------|-------------|
| --name | Name for the extracted artifact |
| --description | Description of what was learned |
| --preview | Show what would be extracted without saving |
| --append | Append to existing skill/rule instead of creating new |

## Examples

```bash
# Auto-detect what to extract
/learn

# Extract as a new skill
/learn skill --name "handling-webhook-retries"

# Extract as a rule
/learn rule --name "api-versioning-pattern"

# Preview without saving
/learn --preview

# Add to existing skill
/learn --append skills/error-handling
```

## What Gets Extracted

### From Debugging Sessions
```yaml
Pattern: "Root cause analysis for race conditions"
Extracted:
  - Reproduction steps
  - Diagnostic commands used
  - Solution approach
  - Prevention strategies
```

### From Implementation Sessions
```yaml
Pattern: "OAuth2 flow implementation"
Extracted:
  - Architecture decisions
  - Security considerations
  - Error handling patterns
  - Testing strategies
```

### From Review Sessions
```yaml
Pattern: "Common TypeScript pitfalls"
Extracted:
  - Anti-patterns found
  - Recommended alternatives
  - Detection commands
```

## Output Types

### skill
Creates a new Skill in `.claude/skills/`:
```markdown
---
name: [extracted-name]
description: [Use when...] Extracted from session on [date].
---

# [Skill Name]

## Context
[Why this pattern emerged]

## Pattern
[The reusable workflow/approach]

## Examples
[Code from the session]

## Anti-patterns
[What to avoid, if discovered]
```

### rule
Creates a new Rule in `.claude/rules/`:
```markdown
# [Rule Name]

## Constraint
[What must/must not be done]

## Rationale
[Why this matters]

## Examples
[Good vs bad examples from session]

## Enforcement
[How to detect violations]
```

### pattern
Creates a pattern document in `docs/patterns/`:
```markdown
# Pattern: [Name]

## Problem
[What this solves]

## Solution
[How to apply]

## Example
[From the session]

## Related Patterns
[Links to related]
```

## Workflow

```
┌─────────────────────────────────────────┐
│           /learn Workflow               │
└─────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Analyze conversation  │
        │  - Key decisions      │
        │  - Problem/solutions  │
        │  - Commands used      │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Identify patterns     │
        │  - Recurring themes   │
        │  - Novel approaches   │
        │  - Best practices     │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Classify output type  │
        │  skill/rule/pattern   │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Generate artifact     │
        │  - Name               │
        │  - Description        │
        │  - Content            │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Save to appropriate   │
        │  location              │
        └───────────────────────┘
```

## Pattern Detection Heuristics

| Session Characteristic | Likely Output |
|------------------------|---------------|
| Multi-step debugging with clear phases | Skill (debugging workflow) |
| Repeated constraint violations | Rule (guard rails) |
| Novel architecture approach | Pattern (design pattern) |
| TDD cycle for new domain | Skill (domain-specific TDD) |
| Security considerations | Rule (security constraints) |

## Example Output

After a session debugging async race conditions:

```markdown
---
name: debugging-async-race-conditions
description: Use when tests pass/fail inconsistently or async operations interfere. Extracted 2024-01-15.
---

# Debugging Async Race Conditions

Announce: "I'm using the debugging-async-race-conditions skill."

## Detection
Signs you have a race condition:
- Tests pass locally, fail in CI
- Intermittent failures
- Adding `console.log` makes it pass

## Investigation Steps

1. **Identify shared state**
```bash
rg "let |var " --type ts | grep -v const
```

2. **Find async operations**
```bash
rg "async |await |Promise\.|setTimeout|setInterval" --type ts
```

3. **Check for missing awaits**
```bash
# Functions returning promises but not awaited
rg "\.then\(|new Promise" --type ts -A 2
```

## Solution Patterns

### Pattern 1: Condition-based waiting
```typescript
// ❌ Arbitrary timeout
await new Promise(r => setTimeout(r, 1000));

// ✅ Condition-based
await waitFor(() => element.isVisible());
```

### Pattern 2: Proper cleanup
```typescript
beforeEach(() => {
  // Reset shared state
  cache.clear();
});
```

## Prevention
- Use `const` by default
- Avoid shared mutable state
- Always await async operations
- Clean up in test hooks
```

## Integration with CLAUDE.md

Extracted patterns can be referenced in CLAUDE.md:

```markdown
# Project Memory

## Learned Patterns
- debugging-async-race-conditions (2024-01-15)
- api-versioning-strategy (2024-01-10)
- webhook-retry-handling (2024-01-08)

When encountering similar problems, reference these skills.
```

## Related Commands

- `/deploy` - Deploy after learning
- `/update-docs` - Document learned patterns
