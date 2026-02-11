# Notifications API Reference

*Last updated: September 2024*
*Owner: Platform Team (`#team-platform`)*

The Notifications API handles all outbound communications — emails, SMS, push notifications, and webhook deliveries.

## Base URL

- Production: `https://api.novapay.com/v2/notifications`
- Staging: `https://api.staging.novapay.internal/v2/notifications`
- Local dev: `http://localhost:8003/v2/notifications`

## Overview

The Notifications API is an internal-only service. It is NOT exposed to merchants directly. Other NovaPay services call it to trigger notifications based on business events.

All notifications are processed asynchronously via a Kafka message queue. The API accepts the request, enqueues it, and returns immediately. Delivery is best-effort with retries.

## Endpoints

### POST /v2/notifications/send

Sends a notification through one or more channels.

**Request Body:**
```json
{
  "recipient": {
    "merchant_id": "merch_abc123",
    "email": "admin@acme.com",
    "phone": "+14155551234"
  },
  "template": "payment_completed",
  "channels": ["email", "webhook"],
  "data": {
    "payment_id": "pay_xyz789",
    "amount": 5000,
    "currency": "USD"
  },
  "priority": "normal"
}
```

**Priority levels:**
- `critical`: Delivered immediately, bypasses batching (use for security alerts, fraud notifications)
- `high`: Delivered within 1 minute
- `normal`: Delivered within 5 minutes (may be batched)
- `low`: Delivered within 1 hour (batched with other low-priority notifications)

### GET /v2/notifications/status/{notification_id}

Returns delivery status for a specific notification.

**Response:**
```json
{
  "notification_id": "notif_abc123",
  "status": "delivered",
  "channel": "email",
  "delivered_at": "2025-01-15T10:35:22Z",
  "attempts": 1
}
```

### GET /v2/notifications/templates

Lists available notification templates.

### POST /v2/notifications/webhooks/test

Sends a test webhook to a merchant's configured endpoint. Useful for merchant onboarding.

## Notification Templates

Templates are stored in the `notification-templates` repo and deployed via CI. Current templates include:

| Template ID | Channels | Description |
|-------------|----------|-------------|
| `payment_completed` | email, webhook | Payment successfully processed |
| `payment_failed` | email, webhook | Payment processing failed |
| `payment_refunded` | email, webhook | Refund processed |
| `kyc_approved` | email | Merchant KYC verification approved |
| `kyc_rejected` | email | Merchant KYC verification rejected |
| `security_alert` | email, sms | Suspicious activity detected |
| `api_key_created` | email | New API key created |
| `weekly_summary` | email | Weekly transaction summary |

## Retry Policy

Failed deliveries are retried with exponential backoff:
- 1st retry: 30 seconds
- 2nd retry: 2 minutes
- 3rd retry: 15 minutes
- 4th retry: 1 hour
- 5th retry: 6 hours

After 5 failed attempts, the notification is marked as `permanently_failed` and an alert is sent to `#notifications-alerts` on Slack.

## Email Provider

We use **Amazon SES** for transactional emails. The sending domain is `notifications@novapay.com`. SPF, DKIM, and DMARC are configured.

TODO: Migrate to dedicated email provider (SendGrid or Postmark) for better deliverability analytics — tracked in PLAT-4521.
