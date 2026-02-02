# Agent Delegation Rules

This document defines when and how to delegate tasks to specialized agents.

## Core Principle

**The main agent orchestrates; specialized agents execute.**

Do not try to do everything yourself. Delegate to the right specialist.

## Agent Inventory

### Planning Phase

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| `prd-generator` | Generate PRD from ideas | Unclear requirements, new feature requests |
| `architect` | System design, ADR creation | Complex features, architectural decisions |
| `planner` | Task breakdown, plan creation | Before any multi-file implementation |

### Implementation Phase

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| `implementer` | Execute tasks from plan | During task execution |
| `tdd-guide` | TDD workflow guidance | Writing tests, feature implementation |
| `build-error-resolver` | Fix build/compile errors | TypeScript errors, build failures |

### Review Phase

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| `design-reviewer` | Design fidelity check | When design reference (Figma URL, screenshot, mockup) exists and code is implemented |
| `spec-reviewer` | PRD compliance check | After implementation, before merge |
| `code-reviewer` | Code quality review | After implementation, before merge |
| `security-reviewer` | Security audit | Code handling auth, data, APIs |

### Delivery Phase

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| `issue-fixer` | Fix issues from review | After review feedback |
| `doc-updater` | Update documentation | After feature completion |
| `deployer` | Deploy to environment | Ready for deployment |

## Delegation Decision Tree

```
User Request
    │
    ├─ "I have an idea for..." ──────────► prd-generator
    │
    ├─ "Design the architecture for..." ─► architect
    │
    ├─ "Plan the implementation of..." ──► planner
    │
    ├─ "Implement task T001..." ─────────► implementer (with tdd-guide skill)
    │
    ├─ "Fix this build error..." ────────► build-error-resolver
    │
    ├─ "Review code against design..." ──► design-reviewer (when design reference exists)
    │
    ├─ "Review this code..." ────────────► code-reviewer
    │                                       └─► security-reviewer (if auth/data)
    │
    ├─ "Fix the review feedback..." ─────► issue-fixer
    │
    ├─ "Update the docs..." ─────────────► doc-updater
    │
    └─ "Deploy to staging..." ───────────► deployer
```

## Mandatory Delegation Rules

### MUST Delegate

1. **PRD Creation** → `prd-generator`
   - Never create PRD without the specialized agent
   
2. **Task Planning** → `planner`
   - Never start implementation without a plan
   - Plans must use `writing-plans` skill

3. **Code Review** → `spec-reviewer` + `code-reviewer`
   - Always two-stage review
   - Spec first, then quality
   - Never self-review (cognitive isolation required)

4. **Security-Sensitive Code** → `security-reviewer`
   - Authentication/Authorization
   - Data handling
   - API endpoints
   - File operations

5. **Design Fidelity** → `design-reviewer`
   - When any design reference exists (Figma URL, screenshot, design mockup) and code is implemented
   - Not tied to figma-to-code; any code with a design reference qualifies
   - Conditional first stage in review pipeline when design reference exists
   - Figma URLs → Figma MCP mode; image files → screenshot mode

### MAY Delegate

1. **Simple Bug Fixes** - Main agent can handle if < 5 min
2. **Documentation Updates** - Main agent can handle if minor
3. **Configuration Changes** - Main agent can handle

## Agent Communication Protocol

### Dispatching an Agent

```markdown
I need to delegate this to the [agent-name] agent.

**Task**: [Brief description]
**Input**: 
- [Required input 1]
- [Required input 2]

Dispatching [agent-name]...
```

### Receiving Agent Results

```markdown
[agent-name] has completed the task.

**Result Summary**:
[Key findings/outputs]

**Next Steps**:
[What happens next based on the result]
```

## Agent Tool Permissions

| Agent | Read | Write | Edit | Bash | Grep | Glob |
|-------|------|-------|------|------|------|------|
| prd-generator | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| architect | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ |
| planner | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| implementer | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| tdd-guide | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| build-error-resolver | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| design-reviewer | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ |
| spec-reviewer | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| code-reviewer | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ |
| security-reviewer | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ |
| issue-fixer | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| doc-updater | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| deployer | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |

**Key Insight**: Review agents have NO write permissions. They observe and report; they don't fix.

## Subagent vs Direct Execution

### Use Subagent When:
- Task requires "fresh eyes" (code review)
- Task should not know implementation context (spec review)
- Task is independent and well-defined
- Cognitive isolation improves quality

### Execute Directly When:
- Task needs conversation history
- Task is iterative/exploratory
- Task is quick (< 5 min)
- Context switching cost > benefit

## Error Handling

If an agent fails:

1. **Capture the error** - What went wrong?
2. **Assess retry** - Is retry likely to succeed?
3. **Escalate if needed** - Human intervention required?
4. **Log the failure** - For learning and improvement

```markdown
[agent-name] encountered an error:

**Error**: [Description]
**Attempted**: [What was tried]
**Assessment**: [Retry / Escalate / Alternative]

[Action taken]
```

## Anti-Patterns

### ❌ Don't Do This

| Anti-Pattern | Problem | Correct Approach |
|--------------|---------|------------------|
| Self-review | Bias, can't catch own mistakes | Dispatch reviewer subagent |
| Skip planning | Leads to rework | Always use planner first |
| Over-delegation | Unnecessary overhead | Simple tasks can be direct |
| Under-delegation | Quality suffers | Delegate per rules above |
| Wrong agent | Inefficient, errors | Match task to specialist |

## Audit Trail

Every agent delegation should be logged:

```markdown
---
**Delegation Log**
Time: [timestamp]
Task: [description]
Agent: [agent-name]
Input: [summary]
Result: [success/failure + brief]
Duration: [time taken]
---
```
