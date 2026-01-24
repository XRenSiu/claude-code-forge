---
name: design
description: Trigger system architecture design. Use after PRD approval to create technical specifications, ADRs, and architecture diagrams.
---

# /design Command

Invoke the **architect** agent to create comprehensive system design documentation.

## Usage

```bash
# Basic usage with PRD path
/design docs/prd/auth-feature.md

# With specific focus area
/design docs/prd/auth-feature.md --focus "API design"

# With constraints
/design docs/prd/auth-feature.md --constraints "PostgreSQL only, 2 week timeline"

# With existing architecture reference
/design docs/prd/auth-feature.md --existing docs/architecture/system.md
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `prd_path` | ✅ | Path to the approved PRD document |
| `--focus` | ❌ | Specific area to focus on (e.g., "data layer", "security") |
| `--constraints` | ❌ | Technical constraints to consider |
| `--existing` | ❌ | Path to existing architecture documentation |
| `--output` | ❌ | Custom output path (default: `docs/architecture/`) |

## What It Does

1. **Reads the PRD** and extracts technical requirements
2. **Analyzes existing codebase** for integration points
3. **Designs system architecture** with components and data flow
4. **Creates ADRs** for significant technical decisions
5. **Generates diagrams** (Mermaid format)
6. **Outputs design document** to `docs/architecture/[feature]-design.md`

## Output Structure

```
docs/
├── architecture/
│   └── [feature]-design.md    # Main design document
├── adr/
│   ├── [number]-[title].md    # Architecture Decision Records
│   └── ...
└── diagrams/
    └── [feature].mermaid      # Architecture diagrams
```

## Example

```bash
# User has completed PRD for user authentication
/design docs/prd/user-authentication.md

# Output:
# ✅ Created docs/architecture/user-authentication-design.md
# ✅ Created docs/adr/001-jwt-vs-session.md
# ✅ Created docs/adr/002-password-hashing.md
# ✅ Created docs/diagrams/user-authentication.mermaid
```

## Pre-requisites

- ✅ PRD must be approved (reviewed and signed off)
- ✅ PRD should contain clear functional and non-functional requirements

## Next Steps

After design is approved:
```bash
/plan docs/architecture/[feature]-design.md
```

## Related Commands

| Command | Description |
|---------|-------------|
| `/prd` | Generate PRD (previous step) |
| `/plan` | Create task breakdown (next step) |
| `/review` | Review design document |

## Agent Invocation

This command dispatches the **architect** agent:

```yaml
agent: architect
input:
  PRD_PATH: [provided path]
  FOCUS: [if --focus provided]
  CONSTRAINTS: [if --constraints provided]
  EXISTING_ARCH: [if --existing provided]
```

## Notes

- Design documents should be reviewed by the team before proceeding to planning
- For complex systems, multiple design sessions may be needed
- ADRs are immutable once accepted; create new ADRs for changes