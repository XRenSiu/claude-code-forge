# Claude Code Plugins Marketplace

> Six plugins that cover the end-to-end AI-assisted development loop: spec → code → review → debug → deploy, plus design reverse-engineering, persona distillation, and autonomous skill optimization.

**At a glance:**

- **[PDForge](#pdforge)** — single-agent 7-phase pipeline from idea to deploy (brainstorm → PRD → design → plan → TDD → review → deploy)
- **[Forge Teams](#forge-teams)** — the adversarial / multi-agent version of PDForge (red team, parallel implementation, debate at every decision)
- **[Adversarial Debugger](#adversarial-debugger)** — competing hypotheses + devil's advocate for stubborn bugs
- **[Design Clone](#design-clone)** — extract Design DNA from a live website, or pixel-perfect clone it into a Next.js app
- **[Persona Distill](#persona-distill)** — distill a person / expert / rule system into a self-contained, portable persona skill
- **[Skill Evolve](#skill-evolve)** — autonomous Darwin-style hill-climbing optimizer for any existing SKILL.md

## Contents

- [Quick Start](#quick-start)
- [Available Plugins](#available-plugins)
- [Which plugin to use?](#which-plugin-to-use)
- [PDForge](#pdforge)
- [Forge Teams](#forge-teams)
- [Adversarial Debugger](#adversarial-debugger)
- [Design Clone](#design-clone)
- [Persona Distill](#persona-distill)
- [Skill Evolve](#skill-evolve)
- [Marketplace Management](#marketplace-management)
- [Plugin Management](#plugin-management)
- [Contributing](#contributing)

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
# PDForge — idea to production-ready code (single-agent pipeline)
/pdforge --from-idea "Add user authentication" --fix --loop

# Forge Teams — adversarial multi-agent pipeline (debate + parallel + red team)
/forge-teams "Payment system refactor" --team-size medium --fix

# Adversarial Debugger — competing hypotheses for hard bugs
/adversarial-debugging

# Design Clone — Design DNA extraction (--dna-only) or pixel-perfect Next.js clone (--full)
/design-clone https://stripe.com --dna-only
/design-clone https://stripe.com --full

# Persona Distill — shape a person / expert / rule system into a reusable skill
"蒸馏乔布斯作为产品设计 mentor"
"distill my iMessage history with Alice into a friend-schema persona skill"

# Skill Evolve — autonomous Darwin-style optimizer for an existing SKILL.md
/skill-evolve path/to/your-skill/SKILL.md --rounds 5
```

### Update

```bash
# Update marketplace registry (fetch latest plugin list)
/plugin marketplace update XRenSiu/claude-code-forge

# Update all installed plugins
/plugin update pdforge
/plugin update forge-teams
/plugin update adversarial-debugger
/plugin update design-clone
/plugin update persona-distill
/plugin update skill-evolve
```

## Available Plugins

| Plugin | Version | Description | Requires |
|--------|---------|-------------|----------|
| [PDForge](plugins/pdforge/) | 1.14.0 | AI-driven 7-phase product development workflow. Single-agent sequential execution with brainstorming, TDD, three-stage review, and auto-fix loops. | - |
| [Forge Teams](plugins/forge-teams/) | 1.8.0 | Agent Teams version of PDForge. 7-phase adversarial pipeline with multi-agent debate, parallel implementation, red team attacks, adversarial debugging, independent bug fix loop, and requirement verification. 23 agents, 8 skills. | Agent Teams |
| [Adversarial Debugger](plugins/adversarial-debugger/) | 1.0.0 | Multi-agent adversarial debugging. Competing hypotheses investigated in parallel, challenged by devil's advocate, synthesized to true root cause. | Agent Teams |
| [Design Clone](plugins/design-clone/) | 1.0.0 | Design DNA extraction + pixel-perfect website cloning. Browser-MCP-driven CSS introspection produces a 150+ field Design DNA profile; `--full` mode additionally spawns parallel builder agents to generate a Next.js clone. | Browser MCP |
| [Persona Distill](plugins/persona-distill/) | 0.4.0 | Distill any persona (person or rule system) into a self-contained Claude Code skill. 5 skills, 9 schemas, 19 components, 12-dim rubric, 9-phase pipeline (CDM execution-profile + self-containment linter + fingerprint verifier). v0.4.0 security hardening: consent attestation gate, untrusted-corpus delimiters, rubric config range locks, corpus access declaration, 6 runnable parsers (iMessage/email/Twitter/generic/Telegram/Slack). | - |
| [Skill Evolve](plugins/skill-evolve/) | 0.1.1 | Darwin-style autonomous SKILL.md optimizer. 8-dimension rubric + independent-subagent scoring + git-backed ratchet hill-climbing (keep-or-revert) to evolve any skill from initial draft toward 90+. | - |

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

## PDForge

**Version**: 1.14.0 · **Category**: Development · **Requires**: none

Single-agent, sequential 7-phase product development pipeline. Use when one Claude driving a well-specified pipeline is the right tool — fewer moving parts than Forge Teams, lower token cost, deterministic flow.

### PDForge Commands

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

### PDForge 7-Phase Workflow

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

## Forge Teams

**Version**: 1.8.0 · **Category**: Development · **Requires**: Agent Teams (experimental)

Adversarial multi-agent version of PDForge. At every critical decision point — requirements, architecture, implementation, review, debug — two or more agents debate, compete, or cross-validate. Higher token cost than PDForge but catches failure modes a single agent would miss. 23 agents + 8 skills.

### Forge Teams Pipeline

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

### Forge Teams Independent Entry Points

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

**Version**: 1.0.0 · **Category**: Debugging · **Requires**: Agent Teams (experimental)

Parallel multi-agent root-cause analysis for stubborn bugs. 3-5 investigators independently propose and pursue hypotheses; a devil's-advocate stress-tests each; a synthesizer produces a final verdict before writing a reproduction test and fix. Use when you have a bug with several plausible causes and a single-agent debug is churning.

### Adversarial Debugger Flow

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

## Design Clone

**Version**: 1.0.0 · **Category**: Design · **Requires**: Browser MCP

Extract a structured **Design DNA** (150+ fields across design system / design style / visual effects) from any live website, and optionally spawn parallel builder agents to regenerate the site as a pixel-perfect Next.js clone. Uses Browser MCP + `getComputedStyle()` to read actual rendered CSS rather than scraped HTML — captures hover states, gradients, shadows, spacing tokens as the browser computes them.

### Design Clone Flow

```
/design-clone <url> [--dna-only | --full]
    |
    +-- Phase 0: Target Validation
    |       Resolve URL, Browser MCP probe, capture primary viewport
    |
    +-- Phase 1: Design DNA Extraction
    |       Enumerate components in viewport
    |    -> For each: capture getComputedStyle() + bounding box
    |    -> Categorize into design-system / design-style / visual-effects
    |    -> Emit structured design-dna.json (150+ fields)
    |
    +-- [--dna-only] STOP HERE -> design-dna.json only
    |
    +-- Phase 2 (--full): Parallel Clone Build
    |       Spawn N builder agents in parallel (one per page/section)
    |    -> Each consumes design-dna.json + region screenshots
    |    -> Emits Next.js + Tailwind components
    |    -> synthesizer merges into one app
    |
    +-- Phase 3 (--full): Pixel-Diff Verification
            Re-render clone -> diff against original viewports
            -> list of mismatches for iteration
```

Typical uses:
- `--dna-only` — feed a competitor's design tokens into your own brand refresh
- `--full` — bootstrap a marketing clone or comparison prototype

---

## Persona Distill

**Version**: 0.4.0 · **Category**: Knowledge · **Requires**: none

Compile a person, expert, or rule system into a **self-contained Claude Code skill** — a folder you can `cp -r` to anyone, no dependency on this plugin afterwards. Covers five roles via five sub-skills: `distill-meta` (orchestrator), `persona-judge` (12-dim quality rubric + density floor + 3 live tests), `distill-collector` (6 runnable corpus parsers), `persona-router` (cross-persona scheduler), `persona-debate` (multi-persona tournament).

Ships 9 schemas (self / collaborator / mentor / loved-one / friend / public-mirror / public-domain / topic / executor) and 19 reusable components. v0.3.0 added a **CDM-based execution-profile** that turns descriptive persona content into instruction-grade "situation → action" pairs (so the skill knows what to *do*, not just what to *think*). v0.4.0 shipped 7 security/trust hardenings (consent attestation gate, untrusted-corpus delimiters, rubric config lock, fingerprint verifier, self-containment linter, corpus access cross-check, expanded PII redaction).

### Persona Distill 9-Phase Pipeline

```
"蒸馏 Alice 作为 friend schema" | /distill-meta
    |
    +-- Phase 0: Intent + Consent Gate
    |       Identify subject, schema_type; if real-person →
    |       consent-attestation.md must exist at skill root
    |
    +-- Phase 0.5: Schema Decision
    |       Pick 1 of 9 schemas (or community); instantiate skill dir
    |
    +-- Phase 1: Corpus Collection
    |       distill-collector parsers (iMessage/email/Twitter/
    |       generic/Telegram/Slack) + public-web research agents
    |       (4 remaining platforms: WeChat/QQ/Feishu/Dingtalk → spec-only)
    |
    +-- Phase 1.5: Research Review + Access-Level Check
    |       Coverage table, gaps, corpus_access_declared vs schema_type
    |
    +-- Phase 2: Dimension Extraction (parallel)
    |       5-8 sub-agents extract components: identity, expression-dna
    |       (7 axes), mental-models (triple validation), tensions, …
    |
    +-- Phase 2.5: Iterative Deepening
    |       Up to 3 rounds; Jaccard>0.8 early stop; high-confidence
    |       candidates auto-merged
    |
    +-- Phase 3: Skill Assembly
    |       Emit SKILL.md, manifest.json, components/**, knowledge/
    |       (hard-rules embeds Untrusted-Corpus Discipline paragraph)
    |
    +-- Phase 3.5: Conflict Detection
    |       4-type factual contradictions surfaced to conflicts.md
    |       (not resolved — preserves tension)
    |
    +-- Phase 3.7: Execution Profile (public-mirror / mentor only)
    |       CDM 4-sweep: Incident → Timeline → 10-Probe → What-If
    |       -> 8 Macrocognition categories × instruction-grade pairs
    |       -> 3 red-line checks (self-report, RPD style, granularity)
    |
    +-- Phase 3.8: Self-Containment + Fingerprint Gate
    |       6-check linter + independent SHA-256 recompute
    |       -> block Phase 4 on any failure
    |
    +-- Phase 4: Quality Validation
    |       persona-judge: 3 live tests (known/edge/voice) +
    |       12-dim rubric + density floor -> validation-report.md
    |
    +-- Phase 5: Delivery
            Path, trigger words, follow-ups (debate / router / migrate)
```

### Persona Distill Companion Skills

```
persona-judge     — evaluate any persona skill (not just ours) on 12 dims + 3 live tests
persona-router    — "which installed persona best fits this question?"
persona-debate    — round-robin / position-based / free-form tournament among 2-5 personas
distill-collector — 6 runnable stdlib-only parsers + redactor (CN-ADDR, CN-NAME, FLAG:MEDICAL, …)
```

Produced skills are portable: `grep -r "persona-distill" produced-skill/` returns 0.

---

## Skill Evolve

**Version**: 0.1.1 · **Category**: Meta · **Requires**: none

Autonomous Darwin-style optimizer for an existing `SKILL.md`. Independent subagents score each round on 8 dimensions (60 structural + 40 effectiveness) with no leakage between judge and mutator; a git-backed ratchet ensures scores only go up (commit on gain, `git checkout --` on regression). Inspired by Karpathy's autoresearch and alchaincyf/darwin-skill.

### Skill Evolve Flow

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

> Scores only go up: every round either commits the gain or cleanly reverts.

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
