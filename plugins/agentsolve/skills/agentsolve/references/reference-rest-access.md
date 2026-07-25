# REST Access

REST and MCP use the same canonical problem language and async lifecycle.
Problem-type references supply payload shape; this file lists transport
surfaces.

## Endpoint Inventory

- `GET /v1/problems`
- `GET /v1/problems/{problem_type}`
- `GET /v1/problems/{problem_type}/schema`
- `GET /v1/problems/{problem_type}/menu`
- `POST /v1/quotes`
- `POST /v1/jobs`
- `GET /v1/jobs/{job_id}`
- `DELETE /v1/jobs/{job_id}`
- `POST /v1/jobs/{job_id}/disputes`
- `POST /v1/jobs/{job_id}/reexecute`
- `POST /v1/inputs/presign`
- `PUT /v1/inputs/{input_handle}`
- `GET /v1/billing/summary`
- `GET /v1/billing/charges`
- `GET /v1/transparency/changes`
- `GET /v1/transparency/jobs/{job_id}`

`GET /v1/jobs/{job_id}/stream` is optional profile convenience. Correctness
comes from ordinary polling.

## Idempotency

`POST /v1/quotes`, `POST /v1/jobs`, dispute creation, and reexecution creation
carry an idempotency key in the JSON body. Reusing a key with different
material inputs must be treated as an idempotency conflict.

## Job Creation

`POST /v1/jobs` has no implicit routing default. Include exactly one of:

- `auto_route: true` for platform-selected deterministic routing
- `selected_algorithms: ["<solver_admission_id>"]` for one agent-selected solver
- `selected_algorithms: ["<id_1>", "<id_2>", ...]` for a 2 to 10 solver
  portfolio

If the quote requires payment, include exactly one available rail from the
quote's `payment_requirement`. If `requires_payment=false`, omit `payment`.

## Terminal States

Terminal job states for polling are `SETTLED`, `REFUNDED`, `DISPUTED`, and
`SUPERSEDED`. Non-terminal reads should include `recommended_poll_after_ms`.

See [reference-errors-and-retries.md](reference-errors-and-retries.md),
[reference-polling-and-backoff.md](reference-polling-and-backoff.md),
and [reference-large-inputs.md](reference-large-inputs.md).
