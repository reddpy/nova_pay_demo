# Code Review Guidelines

*Last updated: November 2024*
*Owner: Developer Experience Team (`#team-devex`)*

## Why Code Reviews Matter

Code reviews are one of our most important quality gates. They catch bugs, share knowledge across the team, and maintain consistency in our codebase. Every engineer at NovaPay participates in code reviews.

## Requirements

### Approval Rules

- **All PRs require 2 approvals** before merge to `main`
- At least one approver must be from the team that owns the modified service
- For cross-team changes, you need one approver from each affected team
- **No deploys from unreviewed branches** — the CI pipeline enforces this via branch protection rules

### Who Can Approve

- Any engineer at NovaPay can provide a review
- However, at least one approval must be from a "code owner" (defined in `CODEOWNERS` file in each repo)
- New engineers (< 3 months) can review and comment but their approval doesn't count toward the 2-approval requirement

## PR Guidelines

### Size

- Keep PRs under **400 lines of code** when possible
- Large changes should be broken into a stack of smaller PRs
- If a PR must be large (e.g., migration), add a detailed description explaining the structure

### Description

Every PR should have:
- **What**: A clear summary of what the change does
- **Why**: The motivation (link to Jira ticket or RFC)
- **How**: Brief explanation of the approach (if not obvious from the code)
- **Testing**: How you tested the change (unit tests, manual testing, staging verification)

### PR Template

```markdown
## What
Brief description of the change.

## Why
Link to ticket: TEAM-1234

## How
Explanation of approach.

## Testing
- [ ] Unit tests added/updated
- [ ] Tested locally
- [ ] Tested in staging

## Checklist
- [ ] No secrets or credentials in code
- [ ] Database migrations are backward-compatible
- [ ] API changes are backward-compatible
- [ ] Feature flag added (if new feature)
```

## Review Expectations

### For Reviewers

- **Respond within 4 business hours** — don't let PRs sit for days
- Focus on: correctness, security, performance, readability, and test coverage
- Use GitHub's "suggestion" feature for small fixes
- Be constructive and respectful — review the code, not the person
- Approve if the PR is good enough, even if you'd do it differently. Reserve blocking comments for real issues.
- Use comment prefixes:
  - `nit:` — Minor style/preference (non-blocking)
  - `question:` — Asking for clarification
  - `suggestion:` — Non-blocking improvement idea
  - `blocker:` — Must be addressed before merge

### For Authors

- Keep PRs focused and well-described
- Respond to all comments before merging
- Don't merge your own PR without 2 approvals
- If a review is urgent, ping the reviewer on Slack (but don't abuse this)
- Rebase on `main` before merging to avoid conflicts

## Special Cases

### Hotfixes
Emergency fixes (SEV-1/SEV-2) can be merged with **1 approval** from a team lead or senior engineer. The second review should happen post-merge within 24 hours.

### Documentation-Only Changes
PRs that only modify documentation (README, wiki, comments) require **1 approval**.

### Automated PRs
Dependabot and renovation PRs require **1 approval** and passing CI. The codeowner for the affected package should review.
