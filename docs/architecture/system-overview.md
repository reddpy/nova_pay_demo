# NovaPay System Architecture Overview

*Last updated: August 2024*
*Owner: Platform Team (`#team-platform`)*

## High-Level Architecture

NovaPay runs a microservice architecture on AWS, deployed to EKS (Elastic Kubernetes Service) across three availability zones in `us-east-1`. We process approximately 2 million payment transactions per day.

```
                    ┌─────────────┐
                    │  CloudFront │
                    │    (CDN)    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ API Gateway │
                    │  (Kong)     │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
   │ Payments API│ │  Users API  │ │Notifications│
   │  (Go)       │ │  (Python)   │ │   (Python)  │
   └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
          │                │                │
   ┌──────▼──────┐ ┌──────▼──────┐        │
   │payments-core│ │  Auth v1    │        │
   │  (Go)       │ │  (JWT)      │        │
   └──────┬──────┘ └─────────────┘        │
          │                                │
    ┌─────▼─────────────────────────────────┐
    │            Kafka Cluster              │
    │     (Event Streaming Platform)        │
    └─────┬─────────────────────────────────┘
          │
   ┌──────▼──────┐  ┌──────────────┐
   │ PostgreSQL  │  │    Redis     │
   │  (RDS)      │  │ (ElastiCache)│
   └─────────────┘  └──────────────┘
```

## Core Services

### API Gateway (Kong)
- Entry point for all external API traffic
- Handles rate limiting, authentication token validation, request routing
- Deployed as a DaemonSet on every node
- Config managed via declarative Kong config in the `gateway-config` repo

### Payments API (Go)
- REST API for payment operations (initiate, capture, refund, query)
- Stateless — all state is in PostgreSQL
- Horizontally scaled, typically 10-20 pods in production

### Payments Core (Go)
- Internal service that handles the actual payment processing logic
- Integrates with external payment processors (Stripe, Adyen)
- Manages the payment state machine (pending → authorized → captured → settled)
- Communicates with Payments API via gRPC

### Users API (Python/FastAPI)
- Manages merchant accounts, team members, API keys
- Handles KYC verification flow (integrates with Persona for identity verification)
- Serves the merchant dashboard backend

### Auth v1 (JWT-based Authentication Service)
- Handles authentication and session management
- Issues JWT tokens for API access and dashboard sessions
- Manages API key validation
- Deployed as a shared service used by all APIs

### Notifications Service (Python/FastAPI)
- Sends emails (via SES), SMS (via Twilio), and webhook deliveries
- Consumes events from Kafka and triggers appropriate notifications
- Uses a template engine for consistent messaging

## Data Stores

### PostgreSQL (RDS)
- Primary data store for all transactional data
- Multi-AZ deployment with automated failover
- Three clusters: `payments-db`, `users-db`, `analytics-db`

### Redis (ElastiCache)
- Used for caching, session storage, and rate limiting
- Cluster mode enabled with 3 shards

### Kafka (MSK)
- Event streaming backbone
- Key topics: `payment.events`, `merchant.events`, `notification.requests`
- 30-day retention on all topics

## Infrastructure

- **Kubernetes**: EKS 1.28, managed node groups with spot instances for non-critical workloads
- **CI/CD**: GitHub Actions for CI, ArgoCD for CD
- **Monitoring**: Datadog for metrics, logs, and APM traces
- **Secrets**: AWS Secrets Manager
- **DNS**: Route 53 with internal hosted zone `novapay.internal`

## Key Metrics

- Average daily transaction volume: ~2M
- API Gateway p99 latency: < 100ms
- Payment processing p99 latency: < 3s (end-to-end)
- System uptime target: 99.99%
