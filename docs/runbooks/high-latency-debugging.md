# Runbook: High Latency Debugging

*Owner: Platform Team (`#team-platform`)*
*Severity: SEV-2 (degraded performance) or SEV-3 (intermittent slowness)*
*Last updated: January 2025*

## Symptoms

- Datadog alert: `p99_latency > 2000ms` on any service
- Merchant complaints about slow API responses
- Dashboard loading times > 5 seconds
- Increased timeout errors in application logs

## Step 1: Identify the Bottleneck

Start with the API Gateway — it has tracing enabled and can show you where time is being spent.

```bash
# Check gateway latency metrics (last 15 minutes)
novapay metrics gateway --window 15m
```

Look at the Datadog APM trace waterfall for slow requests. Key things to check:

1. **Which service is slow?** The gateway trace shows downstream service call durations.
2. **Is it all requests or specific endpoints?** Filter by endpoint path.
3. **When did it start?** Correlate with deploy times (`#deploy-notifications`).

## Step 2: Common Causes

### Database Query Performance

Most latency issues trace back to slow database queries.

```bash
# Connect to the relevant database and check slow queries
psql -h payments-db.cluster-abc123.us-east-1.rds.amazonaws.com -U readonly

-- Find queries running longer than 1 second
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND query_start < now() - interval '1 second'
ORDER BY duration DESC;
```

**Common fixes:**
- Missing index: Check `EXPLAIN ANALYZE` for sequential scans on large tables
- N+1 queries: Check application logs for repeated similar queries
- Lock contention: Check `pg_locks` for blocked queries

### Redis Cache Misses

If cache hit rate drops below 90%, cache misses may be causing extra database load.

```bash
redis-cli -h payments-cache.novapay.internal info stats | grep hit_rate
```

If hit rate is low:
- Check if a recent deploy changed cache keys (common mistake)
- Check if cache TTLs were reduced
- Check Redis memory usage — evictions happen when memory is full

### Kafka Consumer Lag

Async processing delays can cause apparent latency for operations that depend on event processing.

```bash
novapay kafka lag --group payments-processor
```

If lag > 1000 messages, scale up consumers or check for poison messages blocking the queue.

### Network Issues

Rare but possible. Check inter-AZ latency:

```bash
novapay network check --service payments-api
```

## Step 3: Quick Mitigations

| Issue | Quick Fix | Permanent Fix |
|-------|-----------|---------------|
| Slow query | Kill the query, add index | Optimize query, add to slow query log |
| Cache miss storm | Warm the cache manually | Fix cache key generation |
| High pod CPU | Scale up replicas | Profile and optimize hot paths |
| Kafka lag | Scale consumers | Optimize consumer processing |

## Alerting Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| p50 latency | > 200ms | > 500ms |
| p99 latency | > 1000ms | > 2000ms |
| Error rate | > 1% | > 5% |
| DB query time | > 100ms avg | > 500ms avg |

## Escalation

- If latency affects payments processing: Escalate to SEV-1 and follow the [Payments Service Down](./payments-service-down.md) runbook
- If database-related: Ping Platform team on-call
- If network-related: Contact AWS Support via the Support Console
