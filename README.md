# Claude Code Plugins Marketplace

> A curated collection of plugins for Claude Code, enhancing your AI-powered development workflow.

## Quick Start

### Step 1: Add Marketplace

```bash
/plugin marketplace add XRenSiu/claude-code-forge
```

### Step 2: Install Plugin

```bash
# Install PDForge
/plugin install pdforge@XRenSiu/claude-code-forge
```

### Step 3: Use Plugin

```bash
# Full pipeline: idea -> production-ready code
/pdforge --from-idea "Add user authentication" --fix --loop
```

### Update

```bash
# Update marketplace registry (fetch latest plugin list)
claude plugin marketplace update claude-code-forge

# Update installed plugin
claude plugin update pdforge@claude-code-forge

# Update to project scope only
claude plugin update pdforge@claude-code-forge --scope project
```

## Available Plugins

| Plugin | Description | Features |
|--------|-------------|----------|
| [PDForge](plugins/pdforge/) | AI-driven 7-phase product development workflow | Commands: `/pdforge`, `/brainstorm`, `/prd`, `/design`, `/plan`, `/tdd`, `/review`, `/accept`, `/fix`, `/deploy` |

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

# Install plugin
/plugin install pdforge@XRenSiu/claude-code-forge

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
