# Incident Response Process

*Last updated: January 2025*
*Owner: SRE Team (`#sre`)*

## Severity Levels

| Level | Definition | Response Time | Example |
|-------|------------|---------------|---------|
| SEV-1 | Complete outage or data loss | 5 minutes | Payments processing down, data breach |
| SEV-2 | Major feature degraded | 15 minutes | Payment success rate < 95%, dashboard down |
| SEV-3 | Minor feature affected | 1 hour | Notification delays, non-critical API errors |
| SEV-4 | Cosmetic or minor issue | Next business day | Typo on dashboard, minor UI bug |

## Incident Lifecycle

### 1. Detection
Incidents can be detected by:
- **Automated monitoring**: Datadog alerts trigger PagerDuty for SEV-1/SEV-2
- **Manual reports**: Engineers or customers report issues in `#incidents`
- **Merchant support tickets**: Support team escalates via `#support-escalation`

### 2. Declaration
When an incident is detected:

```
/incident declare "Brief description" --severity SEV-X
```

This Slack command (in `#incidents`):
- Creates an incident channel `#inc-YYYY-MM-DD-description`
- Pages the relevant on-call engineer
- Creates a Jira incident ticket
- Posts to `#engineering` and `#incidents`

### 3. Roles

| Role | Responsibility |
|------|---------------|
| **Incident Commander (IC)** | Coordinates the response, communicates status, makes decisions |
| **Technical Lead** | Diagnoses and fixes the issue |
| **Communications Lead** | Updates status page, notifies stakeholders |

For SEV-1: IC is automatically the on-call team lead. For SEV-2+: IC is the on-call engineer.

### 4. Response

- **Join the incident channel** immediately
- **Assess impact**: How many merchants affected? What's the blast radius?
- **Communicate**: Post updates every 15 minutes (SEV-1) or 30 minutes (SEV-2)
- **Fix**: Follow the relevant [runbook](../runbooks/) if one exists
- **Mitigate**: If the fix will take time, implement a mitigation (feature flag, rollback, traffic shift)

### 5. Resolution

When the incident is resolved:
```
/incident resolve "Root cause summary"
```

This:
- Updates the incident ticket
- Posts resolution to `#engineering`
- Updates the status page
- Schedules a post-mortem (automatically for SEV-1/SEV-2)

### 6. Post-Mortem

Required for all SEV-1 and SEV-2 incidents. Post-mortem document must include:

- **Timeline**: What happened and when (use UTC timestamps)
- **Root cause**: What caused the incident (be specific, no "human error")
- **Impact**: Duration, number of affected merchants, estimated revenue impact
- **What went well**: Things that helped resolve the incident quickly
- **What went wrong**: Things that slowed down resolution or made the incident worse
- **Action items**: Concrete follow-up tasks with owners and due dates

Post-mortem meetings are **blameless** — we focus on systems and processes, not individuals.

## On-Call Rotation

Each team maintains their own on-call rotation in PagerDuty:
- Rotation length: 1 week
- Primary and secondary on-call for each team
- On-call engineers receive a $500/week stipend
- Expectation: Acknowledge pages within 5 minutes, begin investigation within 15 minutes

## Useful Links

- PagerDuty: `novapay.pagerduty.com`
- Status page: `status.novapay.com` (StatusPage dashboard)
- Incident history: `#incidents` channel in Slack
- Runbooks: `docs/runbooks/` in this repo
