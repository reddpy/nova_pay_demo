# Local Development Setup

*Last updated: January 2025*

Welcome to NovaPay! This guide will get your local development environment up and running.

## Prerequisites

- macOS or Linux (Windows via WSL2 is supported but not recommended)
- Docker Desktop 4.25+
- Node.js 20 LTS
- Python 3.11+
- Go 1.21+ (for the payments-core service)
- AWS CLI v2 configured with your `novapay-dev` profile

## Step 1: Clone the Monorepo

```bash
git clone git@github.com:novapay/novapay-platform.git
cd novapay-platform
```

## Step 2: Install Dependencies

```bash
# Install the NovaPay CLI tool
npm install -g @novapay/cli@latest

# Bootstrap all services
novapay bootstrap
```

This will install dependencies for all services and set up local config files.

## Step 3: Set Up Local Services

```bash
# Start the local infrastructure stack (Postgres, Redis, Kafka, LocalStack)
docker-compose -f docker/docker-compose.local.yml up -d

# Verify everything is running
novapay doctor
```

Expected output from `novapay doctor`:
- PostgreSQL: `localhost:5432` ✅
- Redis: `localhost:6379` ✅
- Kafka: `localhost:9092` ✅
- LocalStack (S3/SQS): `localhost:4566` ✅

## Step 4: Seed the Database

```bash
novapay db:migrate
novapay db:seed
```

This creates test merchants and sample transaction data.

## Step 5: Start Services

```bash
# Start all services in development mode
novapay dev

# Or start specific services
novapay dev --service payments-api
novapay dev --service users-api
novapay dev --service gateway
```

## Service Ports (Local Dev)

| Service | Port |
|---------|------|
| API Gateway | 8080 |
| Payments API | 8001 |
| Users API | 8002 |
| Notifications API | 8003 |
| Dashboard (frontend) | 3000 |
| Admin Panel | 3001 |

## Common Issues

**Port conflicts**: If port 8080 is in use, set `GATEWAY_PORT` in your `.env.local`.

**Docker memory**: Ensure Docker has at least 8GB RAM allocated. The Kafka setup is memory-hungry.

**M1/M2 Macs**: If you hit architecture issues with Docker images, run `export DOCKER_DEFAULT_PLATFORM=linux/amd64` before starting containers.

## Questions?

Reach out in `#dev-environment` on Slack or ping the Developer Experience team.
