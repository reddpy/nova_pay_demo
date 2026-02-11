# API Design Guidelines

*Last updated: November 2024*
*Owner: Developer Experience Team (`#team-devex`)*

## Overview

These guidelines apply to all REST APIs at NovaPay. Consistency across our APIs makes life easier for both our merchants and our engineers.

## URL Structure

- Base URL pattern: `https://api.novapay.com/v{version}/{resource}`
- Use plural nouns for resources: `/payments`, `/merchants`, `/notifications`
- Use kebab-case for multi-word resources: `/api-keys`, `/webhook-endpoints`
- Nest resources only one level deep: `/merchants/{id}/api-keys` (not deeper)
- Version in the URL path, not headers: `/v2/payments`

## HTTP Methods

| Method | Usage | Idempotent |
|--------|-------|------------|
| GET | Retrieve resource(s) | Yes |
| POST | Create resource or trigger action | No |
| PUT | Full resource replacement | Yes |
| PATCH | Partial resource update | No |
| DELETE | Remove resource | Yes |

## Request/Response Format

- Content-Type: `application/json` for all requests and responses
- Use `snake_case` for all JSON field names
- Dates: ISO 8601 format in UTC (`2025-01-15T10:30:00Z`)
- Monetary amounts: Integer in smallest currency unit (cents for USD). `"amount": 5000` means $50.00.
- IDs: Prefixed strings (`pay_abc123`, `merch_def456`). The prefix indicates the resource type.

## Pagination

Use cursor-based pagination for all list endpoints:

```json
{
  "data": [...],
  "has_more": true,
  "next_cursor": "eyJpZCI6MTIzfQ=="
}
```

- Default page size: 20
- Maximum page size: 100
- Cursor is an opaque base64-encoded string (don't assume its format)

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "type": "invalid_request",
    "code": "MISSING_REQUIRED_FIELD",
    "message": "The 'amount' field is required.",
    "param": "amount",
    "request_id": "req_abc123"
  }
}
```

Error types:
- `invalid_request` (400) — Malformed request
- `authentication_error` (401) — Invalid or missing credentials
- `authorization_error` (403) — Valid credentials but insufficient permissions
- `not_found` (404) — Resource doesn't exist
- `conflict` (409) — Resource already exists or state conflict
- `rate_limit` (429) — Rate limit exceeded
- `server_error` (500) — Internal server error

## Rate Limiting

All NovaPay APIs enforce a default rate limit of **500 requests per minute** per API key. Rate limit headers are included in every response:

```
X-RateLimit-Limit: 500
X-RateLimit-Remaining: 423
X-RateLimit-Reset: 1706140800
```

Individual services may override this default with higher limits based on their specific requirements. Rate limit overrides must be documented in the service's API reference.

When rate limited, the API returns `429 Too Many Requests` with a `Retry-After` header.

## Authentication

All external APIs require authentication via API key in the `X-NovaPay-Key` header:

```
X-NovaPay-Key: sk_live_abc123...
```

Internal service-to-service calls use OAuth 2.0 client credentials flow (see [Auth Architecture](../architecture/auth-architecture.md)).

## Versioning

- Major versions in URL path: `/v1/`, `/v2/`
- Breaking changes require a new major version
- Non-breaking additions (new optional fields, new endpoints) can be added to the current version
- Deprecated versions are supported for 12 months after the next version launches
- Currently active versions: v2 (current), v1 (deprecated, end of life March 2025)

## Idempotency

All POST endpoints that create resources must support idempotency via the `Idempotency-Key` header:

```
Idempotency-Key: idk_unique_12345
```

- If the same key is used within 24 hours, the original response is returned
- Keys are scoped to the API key (different merchants can use the same key)
- Keys expire after 24 hours

## Webhooks

For webhook delivery, follow these standards:
- Sign payloads with HMAC-SHA256 using the merchant's webhook secret
- Include a `NovaPay-Signature` header with the signature
- Include a `NovaPay-Timestamp` header for replay protection
- Retry failed deliveries with exponential backoff (see [Notifications API](../api/notifications-api.md))
- Allow merchants to configure multiple webhook endpoints per event type

## Documentation

All APIs must have:
- OpenAPI 3.0 spec in the service's repo (`docs/openapi.yaml`)
- Published documentation on the developer portal
- Code examples in at least Python and JavaScript
- A changelog documenting all changes per version
