# Deployment Process

*Last updated: December 2024*
*Owner: Platform Team (`#team-platform`)*

## Overview

NovaPay uses a continuous deployment model with GitOps. All deployments go through our CI/CD pipeline — there are no manual deployments to production.

## Deployment Pipeline

```
Code Push → GitHub Actions (CI) → Build & Test → Container Image → ArgoCD (CD) → Kubernetes
```

### Step-by-Step

1. **Push to feature branch** and open a Pull Request
2. **CI runs automatically** (GitHub Actions):
   - Linting (ESLint, golangci-lint, ruff)
   - Unit tests
   - Integration tests (against test database)
   - Security scan (Snyk)
   - Container image build
3. **PR is reviewed and approved** (see separate code review guidelines)
4. **Merge to `main`** triggers the deployment pipeline
5. **ArgoCD detects the new image** and begins rollout:
   - Staging is deployed first (automatic)
   - Staging smoke tests run (5-minute window)
   - Production deployment begins (canary rollout)
6. **Canary rollout** (production):
   - 10% of traffic goes to new version
   - Monitor error rates and latency for 5 minutes
   - If healthy: roll out to 50%, then 100%
   - If unhealthy: automatic rollback

## Environment Promotion

| Environment | Trigger | Auto/Manual |
|-------------|---------|-------------|
| Development | Push to any branch | Automatic |
| Staging | Merge to `main` | Automatic |
| Production | Staging smoke tests pass | Automatic (canary) |

## Deploy Schedule

- Deploys can happen **anytime Monday through Thursday**
- **Friday deploys are discouraged** — you need VP Engineering approval for Friday deploys
- **No deploys during active incidents** (deployment pipeline is locked during SEV-1/SEV-2)
- Hotfixes can bypass the schedule with team lead approval

## Rollback

If a production deployment causes issues:

```bash
# Quick rollback via ArgoCD
novapay rollback <service-name>

# Or via kubectl
kubectl rollout undo deployment/<service-name> -n <namespace>
```

Rollbacks take effect within 30 seconds.

## Feature Flags

We use **LaunchDarkly** for feature flags. New features should be behind a flag when possible.

```go
if ld.BoolVariation("new-payment-flow", user, false) {
    // new code path
} else {
    // existing code path
}
```

This allows us to deploy code without enabling features, and to gradually roll out changes.

## Monitoring After Deploy

After every deploy, check:
1. `#deploy-notifications` for the deploy status message
2. Datadog APM for latency and error rate changes
3. Application logs for new error patterns
4. The service's health endpoint

## Required Notifications

- All production deploys are announced in `#deploy-notifications` automatically
- SEV-impacting changes should also be posted in `#engineering`
- Database migrations should be coordinated with Platform team and announced in advance
