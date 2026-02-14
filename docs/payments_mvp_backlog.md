# Payments MVP Backlog (2 Sprints)

## Goal
Enable a simple user flow for non-web3 users:
`fiat -> crypto -> pay ticket / tip`.

Primary providers in MVP:
- MoneyGram (on-ramp/off-ramp via Stellar ecosystem)
- AirTM (regional LATAM fallback and additional fiat rails)

Secondary provider:
- Crossmint (optional fallback for card-based onboarding)

## Scope for MVP
- API contracts for creating payment intents, provider webhooks, and status tracking.
- Provider orchestration with deterministic routing (`moneygram` first, `airtm` fallback).
- Telegram/WebApp integration point through a checkout URL returned by backend.
- Internal status model to track each payment intent end-to-end.

Out of scope for MVP:
- Full SEP-24 implementation inside this repo.
- Final custody/orchestration wallet architecture.
- Smart-contract ticket settlement.

## Sprint 1 (Backend foundation + MoneyGram first path)

### Story 1: Payment intent domain model
- Add `payment_intents` table with statuses, provider data, and references.
- Add migration and indices for status/provider/event lookups.
- Define lifecycle statuses: `pending`, `processing`, `completed`, `failed`, `cancelled`, `expired`.

Acceptance:
- A payment intent can be created and queried by `payment_id`.
- Backend persists checkout URL and provider reference fields.

### Story 2: API contracts
- `POST /api/payments/create`
- `GET /api/payments/{payment_id}/status`
- `POST /api/payments/webhook/{provider}`

Acceptance:
- Contracts are available in OpenAPI.
- Webhook updates persisted status.

### Story 3: MoneyGram integration adapter (MVP-level)
- Route intent to MoneyGram when no provider preference is specified.
- Generate provider checkout URL and attach payment reference.
- Add webhook secret validation env var support.

Acceptance:
- Payment can be created with MoneyGram checkout URL.
- Webhook can move payment from `pending` to terminal status.

### Story 4: Telegram handoff
- Telegram bot/WebApp receives `checkout_url` and opens provider page.
- User can poll status endpoint after checkout.

Acceptance:
- User sees payment status updates in Telegram flow.

## Sprint 2 (AirTM fallback + production hardening)

### Story 5: AirTM adapter and provider routing
- Add provider preference support in `create`.
- Fallback rule: if provider unsupported or unavailable, fallback to default.
- Keep webhook contract identical for both providers.

Acceptance:
- `preferred_provider=airtm` returns AirTM checkout URL.
- AirTM webhook updates payment intent.

### Story 6: Crossmint optional fallback
- Add optional provider gate behind feature flag:
  - `PAYMENT_ENABLE_CROSSMINT=true`
- Reuse same intent lifecycle and webhook/status contracts.

Acceptance:
- Crossmint can be enabled without schema changes.

### Story 7: Reliability and observability
- Add idempotency handling for webhook replays.
- Add retry-safe processing and structured logs.
- Add provider timeout/error dashboards.

Acceptance:
- Duplicate webhook events do not break final status.
- Failed provider calls are visible in logs and metrics.

## API Contracts

## `POST /api/payments/create`
Creates a payment intent and returns checkout URL.

Request:
```json
{
  "event_id": 123,
  "kind": "ticket",
  "fiat_amount": 15000,
  "fiat_currency": "ARS",
  "preferred_provider": "moneygram",
  "telegram_user_id": 987654321,
  "user_wallet": "G...STELLAR_ADDRESS...",
  "metadata": {
    "source": "telegram",
    "chat_id": "-1001234567890"
  }
}
```

Response:
```json
{
  "payment_id": "2e8b8cc4fd934a0f9f5f0f8e4f9f45c0",
  "event_id": 123,
  "provider": "moneygram",
  "status": "pending",
  "checkout_url": "https://moneygram.com/intl/stellarwallets?reference=2e8b8cc4fd934a0f9f5f0f8e4f9f45c0&source=ba-nightlife-bot",
  "fiat_amount": 15000,
  "fiat_currency": "ARS",
  "kind": "ticket",
  "created_at": "2026-02-14T15:00:00.000000Z"
}
```

## `POST /api/payments/webhook/{provider}`
Provider callback endpoint (MoneyGram/AirTM).

Headers:
- `X-Webhook-Secret: <provider secret>` (optional in dev, required in prod when env var is set)

Payload example:
```json
{
  "payment_id": "2e8b8cc4fd934a0f9f5f0f8e4f9f45c0",
  "status": "completed",
  "transaction_id": "mg_9f8e7d6c"
}
```

Response:
```json
{
  "ok": true,
  "payment_id": "2e8b8cc4fd934a0f9f5f0f8e4f9f45c0",
  "provider": "moneygram",
  "status": "completed"
}
```

## `GET /api/payments/{payment_id}/status`
Read current status of payment intent.

Response:
```json
{
  "payment_id": "2e8b8cc4fd934a0f9f5f0f8e4f9f45c0",
  "event_id": 123,
  "provider": "moneygram",
  "status": "processing",
  "provider_status": "pending_kyc",
  "kind": "ticket",
  "fiat_amount": 15000,
  "fiat_currency": "ARS",
  "checkout_url": "https://moneygram.com/intl/stellarwallets?reference=2e8b8cc4fd934a0f9f5f0f8e4f9f45c0&source=ba-nightlife-bot",
  "failure_reason": null,
  "created_at": "2026-02-14T15:00:00.000000Z",
  "updated_at": "2026-02-14T15:02:12.000000Z"
}
```

## Required Environment Variables
- `PAYMENT_MONEYGRAM_CHECKOUT_URL` (optional, default provided)
- `PAYMENT_AIRTM_CHECKOUT_URL` (optional, default provided)
- `PAYMENT_MONEYGRAM_WEBHOOK_SECRET` (recommended in production)
- `PAYMENT_AIRTM_WEBHOOK_SECRET` (recommended in production)

## Integration Notes for Curator Priorities
- Curator anchors are reflected in MVP priority:
  - AirTM as regional rail
  - MoneyGram as core on-ramp/off-ramp bridge
- Crossmint can be added as optional fallback layer without changing API contracts.
