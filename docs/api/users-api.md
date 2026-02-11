# Users API Reference

*Last updated: October 2024*
*Owner: Growth & Merchant Experience Team (`#team-growth`)*

The Users API manages merchant accounts, team members, and API key provisioning.

## Base URL

- Production: `https://api.novapay.com/v2/users`
- Staging: `https://api.staging.novapay.internal/v2/users`
- Local dev: `http://localhost:8002/v2/users`

## Authentication

Requires a valid session token (for dashboard users) or API key (for programmatic access). Admin operations require the `admin` or `owner` role.

## Endpoints

### POST /v2/users/merchants/register

Registers a new merchant account. This kicks off the KYC verification flow.

**Request Body:**
```json
{
  "business_name": "Acme Corp",
  "business_type": "llc",
  "country": "US",
  "contact_email": "admin@acme.com",
  "contact_phone": "+14155551234",
  "website": "https://acme.com"
}
```

**Response (201):**
```json
{
  "merchant_id": "merch_abc123",
  "status": "pending_verification",
  "kyc_reference": "kyc_ref_456",
  "created_at": "2025-01-10T08:00:00Z"
}
```

Note: Merchant accounts are not active until KYC verification is complete. Verification typically takes 1-3 business days.

### GET /v2/users/merchants/{merchant_id}

Returns merchant profile and verification status.

### PUT /v2/users/merchants/{merchant_id}

Updates merchant profile fields. Only allowed for `owner` role.

### POST /v2/users/merchants/{merchant_id}/team

Invites a team member to the merchant's dashboard.

**Request Body:**
```json
{
  "email": "teammate@acme.com",
  "role": "developer",
  "permissions": ["view_payments", "manage_api_keys"]
}
```

Roles: `owner`, `admin`, `developer`, `viewer`

### POST /v2/users/api-keys

Creates a new API key for a merchant.

**Request Body:**
```json
{
  "merchant_id": "merch_abc123",
  "label": "Production Key",
  "environment": "live",
  "permissions": ["payments:write", "payments:read"]
}
```

Keys are returned only once at creation time. They cannot be retrieved later — only revoked and re-created.

### DELETE /v2/users/api-keys/{key_id}

Revokes an API key. Takes effect immediately.

## Pagination

All list endpoints use cursor-based pagination:
```
GET /v2/users/merchants?limit=20&cursor=eyJpZCI6MTIzfQ==
```

## Webhook Events

- `merchant.verified` — KYC verification completed successfully
- `merchant.rejected` — KYC verification failed
- `merchant.suspended` — Merchant account suspended (compliance issue)
- `team_member.invited` — New team member invited
- `api_key.created` — New API key created
- `api_key.revoked` — API key revoked

## Important Notes

- Merchant registration has a rate limit of 10 requests per hour per IP (to prevent abuse)
- PII fields (SSN, EIN, bank account numbers) are encrypted at rest using AWS KMS
- All user actions are audit-logged and retained for 7 years (regulatory requirement)
