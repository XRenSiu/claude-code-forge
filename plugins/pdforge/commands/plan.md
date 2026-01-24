# /plan Command

Create a detailed implementation plan from a PRD or design document.

## Usage

```
/plan <prd-path> [options]
```

## Examples

```bash
# Basic usage - create plan from PRD
/plan docs/prd/user-auth.md

# With design document
/plan docs/prd/user-auth.md --design docs/adr/001-auth-architecture.md

# Specify output format
/plan docs/prd/user-auth.md --format json

# Limit scope
/plan docs/prd/user-auth.md --scope "login and registration only"

# Quick plan for small feature
/plan --quick "Add password reset functionality"
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--design <path>` | Path to architecture/design document | None |
| `--format <md\|json>` | Output format | md |
| `--scope <description>` | Limit planning scope | Full PRD |
| `--output <path>` | Custom output path | `docs/plans/YYYY-MM-DD-<name>.md` |
| `--quick <description>` | Quick plan without PRD | N/A |
| `--no-code` | Generate task list without full code | false |

## What It Does

1. **Reads** the PRD (and design doc if provided)
2. **Activates** the `writing-plans` skill
3. **Dispatches** the `planner` agent
4. **Generates** a detailed implementation plan
5. **Saves** to `docs/plans/`
6. **Asks** which execution mode to use

## Output

The command produces:

1. **Plan Document**: `docs/plans/YYYY-MM-DD-<feature-name>.md`
   - Task breakdown with complete code
   - Dependency graph
   - Verification commands
   - Time estimates

2. **Optional JSON**: `docs/plans/YYYY-MM-DD-<feature-name>.json`
   - Machine-readable format for automation

## After Planning

The command will ask:

```
Plan created with 12 tasks (~35 min estimated).

How would you like to execute?

A) Subagent-Driven Development
   - Each task by fresh subagent
   - Two-stage review (spec + quality)
   - Best for: Production code, complex features

B) Executing-Plans
   - Batch execution with checkpoints
   - Review at milestones
   - Best for: MVPs, rapid iteration

C) Manual
   - I'll execute tasks myself
   - Just save the plan

Choice [A/B/C]:
```

## Integration

This command integrates with:

- **planner** agent - Does the actual planning work
- **writing-plans** skill - Enforces planning standards
- **agents.md** rule - Ensures proper agent delegation

## Error Handling

| Error | Resolution |
|-------|------------|
| PRD not found | Verify path, check if file exists |
| Invalid PRD format | Ensure PRD follows standard template |
| Circular dependencies | Review task dependencies in plan |
| Tasks too large | Planner will auto-split tasks >5 min |

## Notes

- Plans are idempotent: running twice with same PRD updates existing plan
- Plans can be edited manually after generation
- Use `--quick` for small features without formal PRD
