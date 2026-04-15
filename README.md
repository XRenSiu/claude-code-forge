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

# Install Design Clone (pixel-perfect website cloning + Design DNA)
/plugin install design-clone@XRenSiu/claude-code-forge

# Install Persona Distill (distill any persona into a self-contained skill)
/plugin install persona-distill@XRenSiu/claude-code-forge

# Install Skill Evolve (Darwin-style SKILL.md optimizer)
/plugin install skill-evolve@XRenSiu/claude-code-forge
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
/plugin marketplace update XRenSiu/claude-code-forge

# Update installed plugins
/plugin update pdforge
/plugin update forge-teams
/plugin update adversarial-debugger
```

## Available Plugins

| Plugin | Version | Description | Requires |
|--------|---------|-------------|----------|
| [PDForge](plugins/pdforge/) | 1.14.0 | AI-driven 7-phase product development workflow. Single-agent sequential execution with brainstorming, TDD, three-stage review, and auto-fix loops. | - |
| [Forge Teams](plugins/forge-teams/) | 1.8.0 | Agent Teams version of PDForge. 7-phase adversarial pipeline with multi-agent debate, parallel implementation, red team attacks, adversarial debugging, independent bug fix loop, and requirement verification. 23 agents, 8 skills. | Agent Teams |
| [Adversarial Debugger](plugins/adversarial-debugger/) | 1.0.0 | Multi-agent adversarial debugging. Competing hypotheses investigated in parallel, challenged by devil's advocate, synthesized to true root cause. | Agent Teams |
| [Design Clone](plugins/design-clone/) | 1.0.0 | Design DNA extraction + pixel-perfect website cloning. Browser-MCP-driven CSS introspection produces a 150+ field Design DNA profile; `--full` mode additionally spawns parallel builder agents to generate a Next.js clone. | Browser MCP |
| [Persona Distill](plugins/persona-distill/) | 0.2.0 | Distill any persona (person or rule system) into a self-contained Claude Code skill. 5 skills (meta/judge/collector/router/debate), 9 schemas, 18 components, 12-dimension quality rubric, multi-round evaluation. | - |
| [Skill Evolve](plugins/skill-evolve/) | 0.1.0 | Darwin-style autonomous SKILL.md optimizer. 8-dimension rubric + independent-subagent scoring + git-backed ratchet hill-climbing (keep-or-revert) to evolve any skill from initial draft toward 90+. | - |

### Which plugin to use?

| Scenario | Recommended |
|----------|-------------|
| Standard feature development | PDForge |
| Quick prototype / MVP | PDForge (`--mode 0to1`) |
| High-quality / security-critical features | Forge Teams |
| Simple bug fix | Forge Teams `/forge-fix --quick` or PDForge `/fix` |
| Complex bug with multiple possible root causes | Forge Teams `/forge-fix` or Adversarial Debugger |
| Check if a requirement is implemented | Forge Teams `/forge-verify` |
| Verify + auto-implement missing features | Forge Teams `/forge-verify --fix` |
| Need parallel implementation acceleration | Forge Teams |
| Clone a live website (design DNA or pixel-perfect Next.js) | Design Clone |
| Distill a persona / expert / rule system into a skill | Persona Distill |
| Improve quality of an existing SKILL.md | Skill Evolve |

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

### Independent Entry Points

```
/forge-fix "bug description" [--quick] [--loop N]
    |
    +-- Quick Path (--quick): Locate -> TDD Fix -> Verify
    |
    +-- Full Path: Adversarial Debugging -> TDD Fix -> Independent Verify
    |       3-5 hypothesis-investigators + devil's-advocate + synthesizer
    |       Three-layer loop: Fixer -> Advisor -> Replanner
    |
    +-- Loop until fixed or circuit breaker (max N rounds)

/forge-verify "requirement description" [--fix] [--loop N]
    |
    +-- Phase 0: Structurize (EARS format)
    +-- Phase 1: Code Mapping (Grep + Glob + Read)
    +-- Phase 2: Test Verification (optional)
    +-- Phase 3: Gap Report (5-level classification)
    +-- Phase 4: Auto Fix (--fix: TDD implement missing features)
    +-- Phase 5: Re-Verify (loop until all pass or max N rounds)
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

## Skill Evolve

```
/skill-evolve <path-to-existing-skill>
    |
    +-- Phase 0: Baseline
    |       Independent subagent scores the SKILL.md on 8 dimensions
    |       (60 structural + 40 effectiveness) -> baseline.md
    |
    +-- Phase 1: Hill-Climbing Ratchet (loop N rounds)
    |       Diagnose weakest dimension
    |    -> Atomic mutation (one focused change)
    |    -> Independent re-eval (new subagent, no leak)
    |    -> KEEP (git commit) or REVERT (git checkout --)
    |    -> Append to experiments.tsv
    |
    +-- Phase 2: Final Report
            Baseline vs final scores, improvement list,
            remaining weak dimensions for next iteration
```

> Scores only go up: every round either commits the gain or cleanly reverts. Inspired by Karpathy's autoresearch and alchaincyf/darwin-skill.

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
/plugin install design-clone@XRenSiu/claude-code-forge
/plugin install persona-distill@XRenSiu/claude-code-forge
/plugin install skill-evolve@XRenSiu/claude-code-forge

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
    ├── skills/              # Skills & slash commands (SKILL.md)
    ├── rules/               # Constraints and standards
    ├── hooks/               # Event handlers
    │   └── hooks.json
    └── README.md
```

## Marketplace Registry

See [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json) for the machine-readable plugin index.

## License

MIT License. Individual plugins may have their own licenses.
