# NovaPay Engineering Team Structure

*Last updated: December 2024*

NovaPay engineering is organized into five main teams, plus a few cross-cutting functions. We're about 200 engineers total across all teams.

## Team Breakdown

### Payments Team (~50 engineers)
**Lead**: Sarah Chen | **Slack**: `#team-payments`

Owns the core payment processing pipeline — everything from payment initiation to settlement. This includes the Payments API, the transaction processing engine, fraud scoring integration, and the settlement batch system.

Key services: `payments-api`, `payments-core`, `settlement-engine`, `fraud-scorer`

### Platform Team (~40 engineers)
**Lead**: Marcus Johnson | **Slack**: `#team-platform`

Owns shared infrastructure and platform services. This team manages the API gateway, service mesh, database infrastructure, Kafka cluster, and observability stack (Datadog). They also own the CI/CD pipeline and deployment tooling.

Key services: `api-gateway`, `config-service`, `service-registry`, `auth-service`

### Developer Experience (~15 engineers)
**Lead**: Priya Patel | **Slack**: `#team-devex`

Makes other engineers productive. Owns the `novapay` CLI, internal developer portal, documentation site, and local development tooling. Also maintains the shared component library and API SDK.

Key services: `developer-portal`, `novapay-cli`, `sdk-generator`

### Risk & Compliance (~30 engineers)
**Lead**: David Kim | **Slack**: `#team-risk`

Handles KYC/AML, transaction monitoring, sanctions screening, and regulatory reporting. Works closely with the legal and compliance teams.

Key services: `kyc-service`, `transaction-monitor`, `sanctions-screener`, `compliance-reporter`

### Growth & Merchant Experience (~35 engineers)
**Lead**: Alex Rivera | **Slack**: `#team-growth`

Owns the merchant-facing dashboard, onboarding flows, merchant API, and analytics. Focused on merchant acquisition and retention.

Key services: `merchant-dashboard`, `merchant-api`, `analytics-service`, `onboarding-flow`

## Cross-Cutting Functions

### SRE / On-Call
We have a shared SRE team (~15 engineers) that manages production infrastructure, but **each team is responsible for their own on-call rotation**. SRE provides tooling and support, not 24/7 coverage for your services.

### Data Engineering (~15 engineers)
Shared team that manages the data warehouse (Snowflake), ETL pipelines, and real-time event streaming. Reports into Platform but supports all teams.

## Org Chart

```
VP Engineering (Jamie Torres)
├── Payments (Sarah Chen)
├── Platform (Marcus Johnson)
│   └── Data Engineering (Ravi Gupta)
├── Developer Experience (Priya Patel)
├── Risk & Compliance (David Kim)
├── Growth & Merchant Experience (Alex Rivera)
└── SRE (Lisa Park)
```

## How Teams Interact

- All inter-service communication goes through the API Gateway or Kafka events
- Cross-team projects are coordinated through weekly "Tech Leads Sync" (Wednesdays, 2pm PT)
- RFCs for cross-cutting changes go to `#rfc-review` for feedback
- Each team owns their services end-to-end: development, testing, deployment, and on-call
