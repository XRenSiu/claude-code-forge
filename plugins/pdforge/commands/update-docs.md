# /update-docs Command

Synchronize project documentation with code changes.

## Usage

```
/update-docs [scope] [options]
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| scope | No | all | What to update: readme, api, codemap, changelog, all |

## Options

| Option | Description |
|--------|-------------|
| --path | Specific code path to analyze |
| --since | Generate changelog since commit/tag |
| --format | Output format (markdown/openapi/jsdoc) |
| --verify | Verify existing docs without updating |
| --diff | Show what would change without applying |

## Examples

```bash
# Update all documentation
/update-docs

# Update only API documentation
/update-docs api

# Update changelog since last release
/update-docs changelog --since v1.0.0

# Generate codemap for specific directory
/update-docs codemap --path src/api

# Verify docs are in sync (CI use)
/update-docs --verify

# Preview changes without applying
/update-docs readme --diff
```

## Scope Details

### readme
- Project description
- Installation instructions
- Quick start guide
- Environment variables
- Dependencies

### api
- Route definitions
- Request/response schemas
- Authentication requirements
- Status codes
- Examples

### codemap
- Directory structure
- Module purposes
- Key file descriptions
- Dependency graph

### changelog
- New features (Added)
- Modifications (Changed)
- Bug fixes (Fixed)
- Security patches (Security)
- Deprecations (Deprecated)
- Removals (Removed)

## Workflow

1. **Detect Changes**
   - Compare code with existing docs
   - Identify outdated sections
   - Find undocumented APIs

2. **Generate Updates**
   - Extract info from code
   - Apply documentation templates
   - Maintain consistent style

3. **Verify Accuracy**
   - Test code examples
   - Validate links
   - Cross-reference types

4. **Apply Changes**
   - Update doc files
   - Commit with descriptive message

## Agent Invocation

This command invokes the `doc-updater` agent:

```yaml
agent: doc-updater
parameters:
  SCOPE: [from argument]
  CODE_PATH: [from --path]
  SINCE_COMMIT: [from --since]
  FORMAT: [from --format]
```

## Output Files

| Scope | Output Location |
|-------|-----------------|
| readme | README.md |
| api | docs/api/*.md or openapi.yaml |
| codemap | CODEMAP.md or docs/architecture/ |
| changelog | CHANGELOG.md |

## CI Integration

```yaml
# GitHub Actions example
- name: Verify docs in sync
  run: |
    # Run doc verification
    claude /update-docs --verify
    
    # Fail if docs are outdated
    if [ $? -ne 0 ]; then
      echo "Documentation is out of sync!"
      exit 1
    fi
```

## Related Commands

- `/deploy` - Deploy after docs are updated
- `/learn` - Extract documentation patterns
