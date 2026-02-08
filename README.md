# Claude Code Plugins Marketplace

> A curated collection of plugins for Claude Code, enhancing your AI-powered development workflow.

## Quick Start

### Step 1: Add Marketplace

```bash
/plugin marketplace add XRenSiu/claude-code-forge
```

### Step 2: Install Plugin

```bash
# Install PDForge (single-agent product development)
/plugin install pdforge@XRenSiu/claude-code-forge

# Install Forge Teams (multi-agent adversarial development)
/plugin install forge-teams@XRenSiu/claude-code-forge

# Install Adversarial Debugger (multi-agent debugging)
/plugin install adversarial-debugger@XRenSiu/claude-code-forge
```

### Step 3: Use Plugin

```bash
# PDForge: idea -> production-ready code
/pdforge --from-idea "Add user authentication" --fix --loop

# Forge Teams: idea -> adversarial multi-agent pipeline
/forge-teams "Payment system refactor" --team-size medium --fix

# Adversarial Debugger: competing hypotheses debug
/adversarial-debugging
```

### Update

```bash
# Update marketplace registry (fetch latest plugin list)
claude plugin marketplace update claude-code-forge

# Update installed plugins
claude plugin update pdforge@claude-code-forge
claude plugin update forge-teams@claude-code-forge
claude plugin update adversarial-debugger@claude-code-forge
```

## Available Plugins

| Plugin | Version | Description | Requires |
|--------|---------|-------------|----------|
| [PDForge](plugins/pdforge/) | 1.14.0 | AI-driven 7-phase product development workflow. Single-agent sequential execution with brainstorming, TDD, three-stage review, and auto-fix loops. | - |
| [Forge Teams](plugins/forge-teams/) | 1.1.0 | Agent Teams version of PDForge. 7-phase adversarial pipeline with multi-agent debate, parallel implementation, red team attacks, and adversarial debugging. 23 agents, 6 skills. | Agent Teams |
| [Adversarial Debugger](plugins/adversarial-debugger/) | 1.0.0 | Multi-agent adversarial debugging. Competing hypotheses investigated in parallel, challenged by devil's advocate, synthesized to true root cause. | Agent Teams |

### Which plugin to use?

| Scenario | Recommended |
|----------|-------------|
| Standard feature development | PDForge |
| Quick prototype / MVP | PDForge (`--mode 0to1`) |
| High-quality / security-critical features | Forge Teams |
| Simple bug fix | PDForge `/fix` |
| Complex bug with multiple possible root causes | Adversarial Debugger |
| Need parallel implementation acceleration | Forge Teams |

> **Agent Teams** plugins (Forge Teams, Adversarial Debugger) require the experimental Agent Teams feature:
> ```json
> // settings.json
> { "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }
> ```

---

## PDForge Commands

| Command | Phase | Description |
|---------|-------|-------------|
| `/pdforge` | Full | Complete pipeline orchestration |
| `/brainstorm` | 1 | Socratic requirements clarification |
| `/prd` | 1 | Generate product requirements document |
| `/design` | 2 | System design and ADR generation |
| `/plan` | 3 | Create task breakdown |
| `/tdd` | 4 | Test-driven development workflow |
| `/build-fix` | 4 | Fix build/type errors |
| `/review` | 5 | Single code review |
| `/accept` | 5 | Three-stage acceptance review |
| `/fix` | 6 | Systematic issue fixing |
| `/deploy` | 7 | Deploy to environment |
| `/update-docs` | 7 | Update documentation |
| `/learn` | 7 | Extract reusable patterns |

## PDForge 7-Phase Workflow

```
/pdforge --from-idea "your feature"
    |
    +-- Phase 1: Requirements Analysis
    |       brainstorming + prd-generator -> PRD.md
    |
    +-- Phase 2: System Design
    |       architect -> ADR + Architecture docs
    |
    +-- Phase 3: Task Planning
    |       planner -> 2-5 min task plans + dependencies
    |
    +-- Phase 4: Development Implementation
    |       implementer + tdd-guide -> Code + Tests
    |
    +-- Phase 5: Quality Review
    |       spec-reviewer + code-reviewer + security-reviewer
    |
    +-- Phase 6: Fix Verification
    |       issue-fixer + systematic-debugging
    |
    +-- Phase 7: Delivery Deployment
            deployer + doc-updater -> Production
```

## Forge Teams Pipeline

```
/forge-teams "your feature" --team-size medium
    |
    +-- Phase 1: Requirements Debate
    |       product-advocate vs technical-skeptic -> Consensus PRD
    |
    +-- Phase 2: Architecture Bakeoff
    |       architect A vs architect B + critic + arbiter -> Winning ADR
    |
    +-- Phase 3: Planning + Risk Review
    |       task-planner + risk-assessor -> Risk-reviewed Plan
    |
    +-- Phase 4: Parallel Implementation
    |       team-implementer(s) + quality-sentinel -> Code + Tests
    |
    +-- Phase 5: Red Team Review
    |       red-team + code/security/spec/design reviewers + synthesizer
    |
    +-- Phase 6: Adversarial Debugging (if issues found)
    |       hypothesis-investigators + devil's-advocate + synthesizer
    |
    +-- Phase 7: Cross Acceptance + Deployment
            acceptance-reviewers + doc-updater + deployer
```

## Adversarial Debugger

```
/adversarial-debugging
    |
    +-- Phase 0: Problem Intake
    |       Collect error messages, repro steps, environment info
    |
    +-- Phase 1: Hypothesis Generation
    |       Generate 3-5 independent, falsifiable hypotheses
    |
    +-- Phase 2: Team Assembly
    |       Spawn investigators + devil's advocate + synthesizer
    |
    +-- Phase 3: Adversarial Debate (2-3 rounds)
    |       Investigate -> Report -> Challenge -> Respond -> Synthesize
    |
    +-- Phase 4: Verdict & TDD Fix
            Root cause verdict -> Reproduction test -> Fix -> Verify
```

---

## Marketplace Management

```bash
# Add this marketplace
/plugin marketplace add XRenSiu/claude-code-forge

# Update marketplace (fetch latest plugins)
/plugin marketplace update XRenSiu/claude-code-forge

# List marketplaces
/plugin marketplace list

# Remove marketplace
/plugin marketplace remove XRenSiu/claude-code-forge
```

## Plugin Management

```bash
# List installed plugins
/plugin list

# Install plugins
/plugin install pdforge@XRenSiu/claude-code-forge
/plugin install forge-teams@XRenSiu/claude-code-forge
/plugin install adversarial-debugger@XRenSiu/claude-code-forge

# Update plugin
/plugin update pdforge

# Uninstall plugin
/plugin uninstall pdforge

# Show plugin info
/plugin info pdforge
```

## Contributing

Want to add your own plugin? See [CONTRIBUTING.md](CONTRIBUTING.md).

### Plugin Structure

```
plugins/
└── your-plugin/
    ├── .claude-plugin/
    │   └── plugin.json      # Plugin manifest (required)
    ├── agents/              # AI agent definitions
    ├── commands/            # Slash commands
    ├── skills/              # Reusable workflows
    ├── rules/               # Constraints and standards
    ├── hooks/               # Event handlers
    │   └── hooks.json
    └── README.md
```

## Marketplace Registry

See [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json) for the machine-readable plugin index.

## License

MIT License. Individual plugins may have their own licenses.
