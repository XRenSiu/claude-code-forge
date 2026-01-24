# Contributing to Claude Code Plugins Marketplace

Thank you for your interest in contributing to the Claude Code Plugins Marketplace!

## Adding a New Plugin

### 1. Plugin Requirements

Your plugin must:
- Follow the Claude Code plugin specification
- Include a valid `.claude-plugin/plugin.json` manifest
- Include a `README.md` with documentation
- Include a `LICENSE` file (or inherit from marketplace)
- Be tested and functional

### 2. Directory Structure

```
plugins/
└── your-plugin-name/
    ├── .claude-plugin/
    │   └── plugin.json      # Required: Plugin manifest
    ├── agents/              # Optional: Agent definitions (*.md)
    ├── commands/            # Optional: Command definitions (*.md)
    ├── skills/              # Optional: Skill definitions (SKILL.md)
    ├── rules/               # Optional: Constraint rules (*.md)
    ├── hooks/
    │   └── hooks.json       # Optional: Event handlers
    ├── docs/                # Optional: Additional documentation
    ├── README.md            # Required: Documentation
    └── LICENSE              # Recommended: License file
```

### 3. Plugin Manifest (.claude-plugin/plugin.json)

```json
{
  "name": "your-plugin",
  "description": "Clear, concise description of your plugin",
  "version": "1.0.0",
  "author": {
    "name": "Your Name",
    "email": "your@email.com"
  },
  "homepage": "https://github.com/your/repo",
  "repository": "https://github.com/your/repo",
  "license": "MIT",
  "keywords": ["relevant", "keywords"]
}
```

**Note**: Commands, agents, skills, and hooks are auto-discovered from their respective directories. You don't need to list them in plugin.json.

### 4. Submission Process

1. Fork this repository
2. Create your plugin in `plugins/your-plugin-name/`
3. Add your plugin entry to `.claude-plugin/marketplace.json`
4. Submit a Pull Request

### 5. Marketplace Entry Format

Add your plugin to `.claude-plugin/marketplace.json`:

```json
{
  "name": "your-plugin",
  "description": "Your plugin description",
  "version": "1.0.0",
  "author": {
    "name": "Your Name",
    "email": "your@email.com"
  },
  "source": "./plugins/your-plugin",
  "category": "development",
  "homepage": "https://github.com/...",
  "repository": "https://github.com/...",
  "license": "MIT",
  "tags": ["tag1", "tag2"]
}
```

### 6. Review Criteria

Your plugin will be reviewed for:
- **Functionality**: Does it work as described?
- **Code Quality**: Is it well-structured and maintainable?
- **Documentation**: Is the README clear and complete?
- **Security**: Does it follow security best practices?
- **Originality**: Does it provide unique value?

## Updating an Existing Plugin

1. Make your changes in the plugin directory
2. Update the version in `.claude-plugin/plugin.json`
3. Update the version in `.claude-plugin/marketplace.json`
4. Submit a Pull Request with a clear changelog

## Code of Conduct

- Be respectful and constructive
- Follow the plugin specification
- Test your changes thoroughly
- Document breaking changes

## Questions?

Open an issue for questions or suggestions.
