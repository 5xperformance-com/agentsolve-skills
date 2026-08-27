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

The autonomous paid lane is not active: the approved country allowlist is
empty and staging/production require it off. Do not guess absent registration
or token endpoints. MCP has no separate bootstrap tool.

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

Public requests use inline canonical JSON capped at `1 MiB`. Upload handles are
disabled outside local development; larger payloads are not accepted in the
current public posture.

## Authorization

Send the managed API credential as an HTTP bearer token. Discovery and public
transparency-change metadata are public. Tenant operations require exactly the
published scope:

- `read`: job, dispute, and job-transparency reads;
- `quote:create`: quotes;
- `job:create`: jobs and quote-bound Stripe PaymentIntent preflight;
- `job:write`: cancellation, disputes, and reexecution;
- `billing:read`: billing summary, itemized charges, balance, and authority
  listing; and
- `billing:write`: top-ups, funding links, and authority create/revoke.

An empty scope set grants nothing. `mcp:*` never substitutes for a billing
scope.

The Stage 0 profile exposes no server-sent-event stream. Poll
`GET /v1/jobs/{job_id}` until the job is terminal; that is the only completion
mechanism, and the contract loses nothing by it.

## Idempotency

`POST /v1/quotes`, `POST /v1/jobs`, dispute creation, and reexecution creation
carry an idempotency key in the JSON body. Reusing a key with different
material inputs must be treated as an idempotency conflict.

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
