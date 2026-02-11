# Payments API Reference

*Last updated: January 2025*
*Owner: Payments Team (`#team-payments`)*

The Payments API is NovaPay's core service for processing payment transactions. All payment operations go through this API.

## Base URL

- Production: `https://api.novapay.com/v2/payments`
- Staging: `https://api.staging.novapay.internal/v2/payments`
- Local dev: `http://localhost:8001/v2/payments`

## Authentication

All requests require a valid API key in the `X-NovaPay-Key` header and a merchant ID in `X-Merchant-ID`.

## Rate Limiting

The Payments API enforces a rate limit of **1000 requests per minute** per merchant. This is higher than our standard rate limit because payment processing is latency-sensitive and merchants often send bursts during peak hours. Rate limit headers are included in every response:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1706140800
```

If you exceed the rate limit, you'll receive a `429 Too Many Requests` response.

## Endpoints

### POST /v2/payments/initiate

Creates a new payment intent.

**Request Body:**
```json
{
  "amount": 5000,
  "currency": "USD",
  "merchant_id": "merch_abc123",
  "customer_email": "customer@example.com",
  "payment_method": "card",
  "idempotency_key": "idk_unique_12345",
  "metadata": {
    "order_id": "ord_789"
  }
}
```

**Response (201):**
```json
{
  "payment_id": "pay_xyz789",
  "status": "pending",
  "amount": 5000,
  "currency": "USD",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### GET /v2/payments/{payment_id}

Retrieves payment details by ID.

### POST /v2/payments/{payment_id}/capture

Captures an authorized payment. Must be called within 7 days of authorization.

### POST /v2/payments/{payment_id}/refund

Initiates a full or partial refund.

**Request Body:**
```json
{
  "amount": 2500,
  "reason": "customer_request"
}
```

### GET /v2/payments/list

Lists payments with filtering and pagination.

**Query Parameters:**
- `merchant_id` (required)
- `status`: `pending`, `completed`, `failed`, `refunded`
- `from_date`, `to_date`: ISO 8601 date range
- `limit`: max 100, default 20
- `cursor`: pagination cursor

## Webhooks

Payment status changes trigger webhooks to the merchant's configured endpoint. Events include:
- `payment.completed`
- `payment.failed`
- `payment.refunded`
- `payment.disputed`

Webhook payloads are signed with HMAC-SHA256 using the merchant's webhook secret.

## Error Codes

| Code | Meaning |
|------|---------|
| `INSUFFICIENT_FUNDS` | Card has insufficient funds |
| `CARD_DECLINED` | Card was declined by issuer |
| `INVALID_CURRENCY` | Unsupported currency code |
| `DUPLICATE_PAYMENT` | Idempotency key already used |
| `MERCHANT_SUSPENDED` | Merchant account is suspended |

## SDK Examples

```python
from novapay import NovaPay

client = NovaPay(api_key="sk_live_...")
payment = client.payments.create(
    amount=5000,
    currency="USD",
    payment_method="card"
)
```
