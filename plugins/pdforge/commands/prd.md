---
description: Generate comprehensive PRD from brief requirement description. Analyzes codebase, infers missing details, and validates quality automatically.
argument-hint: <requirement-file-or-inline> [--output <path>]
---

## Mission

Quick access to PRD generation. Wrapper for `prd-generator` subagent.

## Usage

```bash
# From inline idea
/prd "Add user authentication with OAuth2 and JWT"

# From requirement file
/prd docs/ideas/payment-v2.md

# With custom output path
/prd "Dark mode feature" --output docs/prd/dark-mode.md
```

## Behavior

1. Parse input (file or inline text)
2. Invoke `prd-generator` subagent
3. Save PRD to output path (default: `docs/prd/[feature]-prd.md`)
4. Display quality validation results

## Output

- PRD document with all 15 standard sections
- Quality validation score (13 checks)
- Task breakdown hints for planning phase

## Next Step

After PRD generation:
```bash
/plan docs/prd/[feature]-prd.md
```

Or run full pipeline:
```bash
/pdforge --from-prd docs/prd/[feature]-prd.md --fix --loop
```
