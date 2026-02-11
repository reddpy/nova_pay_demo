# Runbook: Database Failover

*Owner: Platform Team (`#team-platform`)*
*Severity: SEV-1 if primary DB is down; SEV-2 if replica lag*
*Last tested: November 2024*

## Overview

NovaPay uses Amazon RDS for PostgreSQL with Multi-AZ deployments. We have three main database clusters:

| Cluster | Endpoint | Purpose |
|---------|----------|---------|
| `payments-db` | `payments-db.cluster-abc123.us-east-1.rds.amazonaws.com` | Payment transactions, merchant data |
| `users-db` | `users-db.cluster-def456.us-east-1.rds.amazonaws.com` | User accounts, API keys, sessions |
| `analytics-db` | `analytics-db.cluster-ghi789.us-east-1.rds.amazonaws.com` | Read replicas for analytics queries |

Each cluster has a primary writer instance and two read replicas in different AZs.

## Automatic Failover

RDS Multi-AZ handles most failover scenarios automatically. When the primary fails:

1. RDS detects the failure (typically within 30 seconds)
2. DNS endpoint flips to the standby instance
3. New primary is available (total downtime: 1-3 minutes)
4. Applications reconnect automatically via connection pooling

**You usually don't need to do anything.** The failover is automatic. Monitor and verify.

## When Manual Intervention Is Needed

### Scenario 1: Replica Lag > 30 seconds

```bash
# Check replica lag
aws rds describe-db-instances --db-instance-identifier payments-db-replica-1 \
  --query 'DBInstances[0].StatusInfos'
```

If replica lag exceeds 30 seconds:
1. Check for long-running queries on the primary: `SELECT * FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '5 minutes';`
2. Check for large batch operations that might be causing write amplification
3. If a specific query is the problem, consider killing it: `SELECT pg_cancel_backend(pid);`

### Scenario 2: Failover Didn't Complete

If the automatic failover is stuck (status shows `failing-over` for > 5 minutes):

```bash
# Force a reboot with failover
aws rds reboot-db-instance \
  --db-instance-identifier payments-db-primary \
  --force-failover
```

### Scenario 3: Connection Pool Exhaustion After Failover

Applications may hold stale connections after failover. If you see `connection refused` errors:

```bash
# Restart application pods to force new connections
kubectl rollout restart deployment/payments-api -n payments
kubectl rollout restart deployment/users-api -n users
```

## Monitoring

- **Datadog dashboard**: "RDS Database Health" (link in `#platform-dashboards` pinned messages)
- **Alerts**: Configured for replica lag > 10s, connection count > 80%, CPU > 90%, storage > 85%
- **CloudWatch**: RDS performance insights for query-level analysis

## Important Notes

- **Never manually promote a read replica** unless directed by Platform team lead. Promotion is irreversible and creates a new standalone instance.
- After any failover event, verify that the connection pooler (PgBouncer) has refreshed its connections.
- All database credentials are stored in AWS Secrets Manager and rotated every 90 days.
- Database backups are taken every 6 hours with a retention period of 30 days.
