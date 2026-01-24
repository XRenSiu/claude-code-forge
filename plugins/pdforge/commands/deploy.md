# /deploy Command

Deploy code to target environment with pre-deploy verification.

## Usage

```
/deploy [environment] [options]
```

## Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| environment | Yes | - | Target: staging, production, preview |

## Options

| Option | Description |
|--------|-------------|
| --platform | Deployment platform (vercel/railway/cloudflare/custom) |
| --branch | Branch to deploy (default: current branch) |
| --skip-checks | Skip non-critical checks (hotfix mode) |
| --dry-run | Show what would be deployed without deploying |
| --rollback | Rollback to previous deployment |

## Examples

```bash
# Deploy to staging
/deploy staging

# Deploy to production with specific platform
/deploy production --platform vercel

# Hotfix deployment (skip advisory checks)
/deploy production --skip-checks

# Preview what would be deployed
/deploy staging --dry-run

# Rollback last deployment
/deploy production --rollback
```

## Workflow

1. **Pre-deploy Checks**
   - Run test suite
   - Verify build succeeds
   - Security scan
   - Environment variables check

2. **Deployment**
   - Execute platform-specific deploy
   - Wait for deployment completion
   - Capture deployment URL/ID

3. **Post-deploy Verification**
   - Health check
   - Smoke test
   - Monitor error rate

4. **Report**
   - Deployment status
   - URL/access info
   - Rollback instructions

## Agent Invocation

This command invokes the `deployer` agent:

```yaml
agent: deployer
parameters:
  ENVIRONMENT: [from argument]
  PLATFORM: [from --platform or auto-detect]
  BRANCH: [from --branch or current]
  SKIP_CHECKS: [from --skip-checks]
```

## Pre-requisites

- All tests passing
- Code review approved (for production)
- No uncommitted changes
- Platform CLI installed (vercel/railway/wrangler)

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Deployment successful |
| 1 | Pre-deploy checks failed |
| 2 | Deployment failed |
| 3 | Post-deploy verification failed |

## Related Commands

- `/update-docs` - Update documentation after deploy
- `/learn` - Extract patterns from deployment session
