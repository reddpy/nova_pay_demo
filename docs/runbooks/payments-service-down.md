# Runbook: Payments Service Down

*Owner: Payments Team (`#team-payments`)*
*Severity: SEV-1 — All payment processing is halted*
*Last tested: December 2024*

## Symptoms

- Datadog alert: `payments-api.health_check CRITICAL`
- Merchants reporting `503 Service Unavailable` on payment endpoints
- Dashboard showing spike in failed transactions
- PagerDuty incident triggered for Payments on-call

## Immediate Actions (First 5 Minutes)

1. **Acknowledge the PagerDuty alert** and join `#incident-active` on Slack
2. **Check the Payments API pods in Kubernetes:**
   ```bash
   kubectl get pods -n payments -l app=payments-api
   kubectl logs -n payments -l app=payments-api --tail=100
   ```
3. **Check if this is a full outage or partial:**
   ```bash
   curl -s https://api.novapay.internal/v2/payments/health | jq .
   ```
4. **Check dependent services:**
   - PostgreSQL (payments-db): `kubectl exec -it payments-db-0 -- pg_isready`
   - Redis (payments-cache): `redis-cli -h payments-cache.novapay.internal ping`
   - Kafka: Check `#kafka-alerts` channel

## Common Root Causes

### 1. Database Connection Pool Exhausted
**Symptoms**: Logs show `connection pool exhausted` or `timeout waiting for connection`

**Fix:**
```bash
# Check current connections
kubectl exec -it payments-db-0 -- psql -c "SELECT count(*) FROM pg_stat_activity;"

# If over 200 connections, restart the API pods to release connections
kubectl rollout restart deployment/payments-api -n payments
```

### 2. Bad Deployment
**Symptoms**: Errors started right after a deploy (check `#deploy-notifications`)

**Fix:**
```bash
# Roll back to previous version
kubectl rollout undo deployment/payments-api -n payments

# Verify rollback
kubectl rollout status deployment/payments-api -n payments
```

### 3. Kafka Consumer Lag
**Symptoms**: Payments are accepted but not processing. Kafka consumer lag is high.

**Fix:**
```bash
# Check consumer lag
kafka-consumer-groups.sh --bootstrap-server kafka.novapay.internal:9092 \
  --group payments-processor --describe

# If lag > 10000, scale up consumers
kubectl scale deployment/payments-processor -n payments --replicas=10
```

### 4. Upstream Provider Outage
**Symptoms**: Logs show timeouts to `processor.stripe.com` or `api.adyen.com`

**Fix**: This is outside our control. Enable the fallback processor:
```bash
novapay config set payments.fallback_processor=true
```

## Escalation

- If not resolved in 15 minutes: Page the Payments team lead (Sarah Chen)
- If not resolved in 30 minutes: Page VP Engineering (Jamie Torres)
- If database-related: Page Platform team on-call
- Update the status page at `status.novapay.com` via the StatusPage dashboard

## Post-Incident

- Create a post-mortem doc within 48 hours (template in Notion)
- Schedule a post-mortem review meeting within 1 week
- File follow-up tickets for any action items
- Update this runbook if the root cause was new
