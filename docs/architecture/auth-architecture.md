# Authentication Architecture

*Last updated: January 2025*
*Owner: Platform Team (`#team-platform`)*

## Current State: Auth v2 (OAuth 2.0 + PKCE)

As of **Q3 2024**, NovaPay has migrated to **Auth v2**, a new authentication system based on **OAuth 2.0 with PKCE** (Proof Key for Code Exchange). Auth v1 (the legacy JWT-based system) was **deprecated in Q3 2024** and is scheduled for full decommission by **March 2025**.

## Why We Migrated

Auth v1 had several issues that motivated the migration:
- JWT tokens were long-lived (24 hours) with no revocation mechanism
- No support for fine-grained scopes — tokens were all-or-nothing
- Session management was ad-hoc and inconsistent across services
- No support for third-party OAuth integrations (merchants wanted "Login with NovaPay")

## Auth v2 Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Client     │────▶│  Auth v2     │────▶│   Token      │
│ (Dashboard/  │     │  (OAuth      │     │   Store      │
│  API)        │◀────│   Server)    │◀────│   (Redis)    │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                     ┌──────▼──────┐
                     │  Users DB   │
                     │ (Accounts)  │
                     └─────────────┘
```

### Key Components

**OAuth 2.0 Server** (`auth-service` v2.x)
- Built on top of `ory/fosite` (Go library)
- Supports authorization code flow with PKCE (for dashboard)
- Supports client credentials flow (for service-to-service)
- Token endpoint: `https://auth.novapay.com/oauth/token`
- Authorization endpoint: `https://auth.novapay.com/oauth/authorize`

**Token Format**
- Access tokens: Short-lived opaque tokens (15 minutes)
- Refresh tokens: Long-lived, stored in Redis, rotated on each use
- Tokens include scopes: `payments:read`, `payments:write`, `merchants:read`, `merchants:admin`

**Token Validation**
- Services validate tokens by calling the auth service's introspection endpoint
- Results are cached locally for 60 seconds to reduce load
- Endpoint: `https://auth.novapay.internal/oauth/introspect`

### Scopes

| Scope | Description |
|-------|-------------|
| `payments:read` | Read payment data |
| `payments:write` | Create/modify payments |
| `merchants:read` | Read merchant profile |
| `merchants:admin` | Manage merchant settings |
| `webhooks:manage` | Configure webhooks |
| `api_keys:manage` | Create/revoke API keys |
| `team:manage` | Invite/remove team members |

## Migration Status

| Component | Status |
|-----------|--------|
| Dashboard (merchant-facing) | ✅ Migrated to Auth v2 |
| Payments API | ✅ Migrated to Auth v2 |
| Users API | ✅ Migrated to Auth v2 |
| Notifications API | ✅ Migrated to Auth v2 (internal only) |
| Admin Panel | ⚠️ In progress — target Feb 2025 |
| Legacy merchant SDK (v3.x) | ⚠️ Still using Auth v1 — SDK v4.0 required |

## Auth v1 Deprecation Timeline

- **Q3 2024**: Auth v2 launched, all new integrations use v2
- **Q4 2024**: Dashboard and core APIs migrated to v2
- **Q1 2025**: Auth v1 enters read-only mode (no new tokens issued)
- **March 2025**: Auth v1 fully decommissioned

**Important**: If you're working on any service that still references Auth v1 JWT tokens, you need to migrate to Auth v2. See the migration guide in the `auth-service` repo: `docs/migration-v1-to-v2.md`.

## Local Development

For local dev, the auth service runs at `http://localhost:8010`. Use these test credentials:

```
Client ID: dev-dashboard-client
Client Secret: dev-secret-12345
Test User: admin@novapay.dev / password123
```

These credentials only work in the local dev environment. Do not use them in staging or production.
