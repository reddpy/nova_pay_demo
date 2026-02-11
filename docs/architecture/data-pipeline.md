# Data Pipeline Architecture

*Last updated: December 2024*
*Owner: Data Engineering (under Platform Team)*

## Overview

NovaPay's data pipeline handles the flow of data from operational databases and event streams into our analytics infrastructure. We process approximately 50 million events per day through this pipeline.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  PostgreSQL  │────▶│   Debezium   │────▶│    Kafka     │
│  (RDS)       │ CDC │  (Connect)   │     │   Topics     │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                          ┌───────▼───────┐
                                          │  Kafka Connect │
                                          │  (S3 Sink)     │
                                          └───────┬───────┘
                                                  │
                                          ┌───────▼───────┐
                                          │   S3 Data     │
                                          │   Lake        │
                                          └───────┬───────┘
                                                  │
                                          ┌───────▼───────┐
                                          │  Snowflake    │
                                          │  (Warehouse)  │
                                          └───────┬───────┘
                                                  │
                                          ┌───────▼───────┐
                                          │   Looker      │
                                          │ (Dashboards)  │
                                          └───────────────┘
```

## Components

### Change Data Capture (CDC)
We use **Debezium** to capture row-level changes from PostgreSQL in real-time. This avoids the need for batch ETL jobs and gives us near-real-time analytics.

**Captured tables:**
- `payments.transactions` — All payment transactions
- `payments.refunds` — Refund records
- `users.merchants` — Merchant profiles
- `users.api_keys` — API key usage tracking

CDC events are published to Kafka topics named `cdc.<schema>.<table>`.

### S3 Data Lake
Raw events land in S3 in Parquet format, partitioned by date:
```
s3://novapay-data-lake/
├── raw/
│   ├── payments/transactions/dt=2025-01-15/
│   ├── payments/refunds/dt=2025-01-15/
│   └── events/payment.events/dt=2025-01-15/
├── processed/
│   ├── daily_transaction_summary/
│   └── merchant_analytics/
└── archive/
```

### Snowflake Data Warehouse
Our analytics warehouse. Organized into three layers:

| Schema | Purpose | Refresh |
|--------|---------|---------|
| `raw` | Direct mirror of S3 data | Continuous (Snowpipe) |
| `staging` | Cleaned and transformed data | Every 15 minutes (dbt) |
| `analytics` | Business-ready models | Every 15 minutes (dbt) |

### dbt (Data Build Tool)
All transformations are managed with dbt. The dbt project lives in the `novapay-analytics` repo.

Key models:
- `fct_transactions` — Fact table for all payment transactions
- `dim_merchants` — Merchant dimension table
- `fct_daily_volume` — Daily transaction volume aggregates
- `fct_merchant_health` — Merchant health scores (churn prediction)

### Looker
Business dashboards and self-serve analytics. Key dashboards:
- **Executive Dashboard**: Daily GMV, transaction counts, success rates
- **Merchant Health**: Per-merchant metrics and trends
- **Operational**: System health, latency, error rates

## Data Freshness SLAs

| Data | Freshness Target | Current |
|------|-------------------|---------|
| Transaction data in Snowflake | < 15 minutes | ~8 minutes avg |
| Daily aggregates | < 1 hour after midnight UTC | ~30 minutes |
| Merchant analytics | < 30 minutes | ~20 minutes |

## Access Control

- Data lake (S3): IAM roles per team, no direct access for individual engineers
- Snowflake: Role-based access. Request access via `#data-access` Slack channel
- Looker: SSO via Okta. Dashboard access based on team membership

## On-Call

Data pipeline issues are handled by the Data Engineering on-call rotation. Alert channel: `#data-pipeline-alerts`.

Common issues and their runbooks are in the `novapay-analytics` repo under `docs/runbooks/`.
