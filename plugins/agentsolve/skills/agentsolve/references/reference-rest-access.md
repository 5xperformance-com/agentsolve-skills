# REST Access

REST and MCP use the same canonical problem language and async lifecycle.
Problem-type references supply payload shape; this file lists transport
surfaces.

## Identity Bootstrap

REST and MCP clients share the HTTP identity control plane:
`GET /.well-known/oauth-protected-resource`, the advertised authorization
metadata, `GET /auth.md`, and authenticated
`POST /v1/identity/bootstrap`. Bootstrap returns stable AgentSolve subject,
account, and logical credential IDs. Exact replay returns those IDs without
redisplaying the one-time migration-recovery code; changed declarations fail
with `IDENTITY_BOOTSTRAP_CONFLICT`.

An unclaimed (autonomous) identity pays for each job with exact x402 USDC from
its own wallet; claiming adds card payments and funded account credit and is
never required to buy. One jurisdiction policy applies to every customer:
AgentSolve serves every jurisdiction except BY, CU, IR, KP, RU, SY, UA-09,
UA-14, UA-40 and UA-43; UA billing must name its region; and x402 is not
offered in AE, BD, CN, ID, NP, TR, UA-23, UA-65 and ZA. A refused jurisdiction
gets no quote (403). A refused rail is marked
`billing_jurisdiction_not_eligible` on the quote and refused at job create with
`payment_jurisdiction_not_allowed`; pay with another available rail. Do not
guess absent registration or token endpoints. MCP has no separate bootstrap
tool.

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
- `POST /v1/quotes`
- `POST /v1/jobs`
- `GET /v1/jobs`
- `GET /v1/jobs/{job_id}`
- `GET /v1/jobs/{job_id}/output`
- `DELETE /v1/jobs/{job_id}`
- `POST /v1/jobs/{job_id}/disputes`
- `POST /v1/jobs/{job_id}/reexecute`
- `GET /v1/disputes/{dispute_id}`
- `GET /.well-known/agentsolve-payments.json`
- `GET /v1/payments/capabilities`
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
[reference-large-inputs.md](reference-large-inputs.md).

## Authorization

Send the managed API credential as an HTTP bearer token. Discovery,
public transparency-change metadata, and the two public feature-request reads
(`GET /v1/feature-requests` and `GET /v1/feature-requests/{feature_request_id}`)
are public. Tenant operations require exactly the published scope:

- `read`: job, dispute, and job-transparency reads, plus your own
  feature-request (`/v1/me/feature-requests`) and bug-report reads;
- `quote:create`: quotes;
- `job:create`: jobs and quote-bound Stripe PaymentIntent preflight;
- `job:write`: cancellation, disputes, reexecution, feature-request and
  bug-report creation, and feature-request votes;
- `billing:read`: billing summary, itemized charges, balance, and authority
  listing; and
- `billing:write`: top-ups, funding links, and authority create/revoke.

An empty scope set grants nothing. `mcp:*` never substitutes for a billing
scope.

The Stage 0 profile exposes no server-sent-event stream. Poll
`GET /v1/jobs/{job_id}` until the job is terminal; that is the only completion
mechanism, and the contract loses nothing by it.

## Idempotency

`POST /v1/quotes`, `POST /v1/jobs`, dispute creation, reexecution creation,
`POST /v1/feature-requests`, and `POST /v1/bug-reports` carry an idempotency
key in the JSON body. Reusing a key with different material inputs must be
treated as an idempotency conflict.

## Feature Requests and Bug Reports

The full lifecycle, statuses and limits are in
[feedback and bug reports](reference-feedback-and-bug-reports.md).

A new feature request or bug report is private and starts `pending_review`;
a feature request also carries your own vote. An operator approval publishes a
feature request. Pending and rejected requests are not searchable, ranked or
votable, and you read them only through your creation response or
`GET /v1/me/feature-requests`. Bug reports are private to you and the operator
in every status. A published request is public, so neither kind may contain
secrets, payloads or personal data, and a declared `blocking` severity does not
bypass screening or limits.

Repeating a creation with the same key returns the stored record with `200` and
spends no new fresh allowance or queue slot. A key reused with different
material or for the other kind is `409 IDEMPOTENCY_CONFLICT`. Identical
material still pending under a new key is `400 INVALID_PAYLOAD` with
`details.rejection_reason=duplicate_pending_submission` and your existing id.

Every attempt spends the request allowance of its kind, including failures and
replays. A fresh item also spends a separate daily quota, and feature and bug
allowances and queues are separate. Votes spend their allowance only when
recorded. A full pending queue is `429 RATE_LIMITED` with `Retry-After: 3600`
and `details.extra.bucket` (`pending_feature_requests` or
`pending_bug_reports`); the interval is a suggestion, not a reserved slot. A
feedback suspension is `403 AUTHENTICATION_REQUIRED` with
`details.rejection_reason=feedback_suspended` on fresh submissions and voting;
reads, replays and vote withdrawal still work. Hidden, foreign and unknown ids
are all `404 JOB_NOT_FOUND`, with `details.field_name` naming
`feature_request_id`, `bug_report_id` or `job_id`. List routes refuse unknown
query parameters with `400`.

## Job Creation

`POST /v1/jobs` has no implicit routing default. Include exactly one of:

- `selected_algorithms: ["<solver_admission_id>"]` for one agent-selected solver
- `selected_algorithms: ["<id_1>", "<id_2>", ...]` for a 2 to 10 solver
  portfolio
- `auto_route: true` for the platform's deterministic catalog-default
  selection (ranked by trust, then quality, then latency, then price)

If the quote bound solver hints — anything submitted under the quote's
`constraints`, including `time_budget_ms` — resubmit the quote's
`effective_solver_hints` verbatim as the job's `solver_hints`; any
divergence is rejected with `QUOTE_HINTS_MISMATCH`.

If the quote requires payment, include exactly one available rail from the
quote's `payment_requirement`. If `requires_payment=false`, omit `payment`.

## Terminal States

Terminal job states for polling are `SETTLED`, `REFUNDED`, `DISPUTED`, and
`SUPERSEDED`. Non-terminal reads should include `recommended_poll_after_ms`.

See [reference-errors-and-retries.md](reference-errors-and-retries.md),
[reference-polling-and-backoff.md](reference-polling-and-backoff.md),
and [reference-large-inputs.md](reference-large-inputs.md).
