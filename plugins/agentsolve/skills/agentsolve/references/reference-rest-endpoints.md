# REST Endpoints, Scopes And Limits

Lookup material for calls beyond a first job, which
[reference-rest-access.md](reference-rest-access.md) walks through.

## Authorization

Send the managed API credential as an HTTP bearer token. Discovery,
public transparency-change metadata, and the two public feature-request reads
(`GET /v1/feature-requests` and `GET /v1/feature-requests/{feature_request_id}`)
are public. Tenant operations require exactly the published scope:

- `read`: job, job-confirmation, dispute, and job-transparency reads, plus your own
  feature-request (`/v1/me/feature-requests`) and bug-report reads;
- `quote:create`: quotes;
- `job:create`: jobs and quote-bound Stripe PaymentIntent preflight;
- `job:write`: cancellation, disputes, reexecution, feature-request and
  bug-report creation, and feature-request votes;
- `billing:read`: billing summary, itemized charges, balance, and authority
  listing; and
- `billing:write`: top-ups, funding links, and authority create/revoke. A
  consumer owner's top-up goes through a funding link, because the REST top-up
  is refused with `consumer_acknowledgement_required`.

An empty scope set grants nothing. `mcp:*` never substitutes for a billing
scope.

## Idempotency

`POST /v1/quotes`, `POST /v1/jobs`, dispute creation, reexecution creation,
`POST /v1/feature-requests`, and `POST /v1/bug-reports` carry an idempotency
key in the JSON body. Reusing a key with different material inputs must be
treated as an idempotency conflict.

## Endpoint Inventory

- `GET /v1/problems`
- `GET /.well-known/oauth-protected-resource`
- `GET /.well-known/oauth-authorization-server`
- `GET /auth.md`
- `POST /v1/identity/bootstrap`
- `GET /v1/problems/{problem_type}`
- `GET /v1/problems/{problem_type}/schema`
- `GET /v1/problems/{problem_type}/menu`
- `GET /v1/problems/{problem_type}/solvers`
- `POST /v1/inputs/presign`
- `PUT /v1/inputs/{input_handle}`
- `POST /v1/quotes`
- `POST /v1/jobs`
- `GET /v1/jobs`
- `GET /v1/jobs/{job_id}`
- `GET /v1/jobs/{job_id}/output`
- `GET /v1/jobs/{job_id}/confirmation`
- `DELETE /v1/jobs/{job_id}`
- `POST /v1/jobs/{job_id}/disputes`
- `POST /v1/jobs/{job_id}/reexecute`
- `GET /v1/disputes/{dispute_id}`
- `GET /.well-known/agentsolve-payments.json`
- `GET /v1/payments/capabilities`
- `GET /v1/payments/faucet-programs`
- `POST /v1/payments/stripe/payment-intents`
- `GET /v1/payments/account-credit/balance`
- `POST /v1/payments/account-credit/top-ups`
- `POST /v1/payments/account-credit/funding-links`
- `POST /v1/payments/authorities`
- `GET /v1/payments/authorities`
- `DELETE /v1/payments/authorities/{payment_authority_id}`
- `GET /v1/billing/summary`
- `GET /v1/billing/charges`
- `GET /v1/transparency/changes`
- `GET /v1/transparency/jobs/{job_id}`
- `POST /v1/feature-requests`
- `GET /v1/feature-requests`
- `GET /v1/feature-requests/{feature_request_id}`
- `GET /v1/me/feature-requests`
- `GET /v1/me/feature-requests/{feature_request_id}`
- `POST /v1/feature-requests/{feature_request_id}/votes`
- `DELETE /v1/feature-requests/{feature_request_id}/votes`
- `POST /v1/bug-reports`
- `GET /v1/bug-reports`
- `GET /v1/bug-reports/{bug_report_id}`

Inline canonical JSON on `POST /v1/quotes` is capped at `16 MiB` after canonical
encoding, and every other request body at `1 MiB`. Upload handles are
available only where a deployment enables them; see
[reference-large-inputs.md](reference-large-inputs.md). Feature requests and
bug reports, with their statuses, limits and refusals, are in
[reference-feedback-and-bug-reports.md](reference-feedback-and-bug-reports.md).
