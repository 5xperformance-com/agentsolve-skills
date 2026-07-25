# MCP Access

MCP is a thin access layer over the same canonical quote -> job -> poll
contract as REST. Tools return quickly and do not wait for compute completion.

## Lifecycle Setup

Stage 0 uses Streamable HTTP at `/mcp` with JSON-RPC POST requests. External MCP
clients should perform authenticated `initialize`, send
`notifications/initialized`, then use `tools/list` and `tools/call`.

Lifecycle is connection setup only. AgentSolve does not issue
`MCP-Session-Id`, does not expose MCP resources or prompts, does not provide
server-push progress streams, and does not ship a stdio package. Use ordinary
job polling for product state. Official Streamable HTTP clients should send
`Accept: application/json, text/event-stream`; the server remains tolerant of
older client headers.

## Tool Inventory

- `agentsolve.problems.list`
- `agentsolve.problems.get`
- `agentsolve.schemas.get`
- `agentsolve.menus.get`
- `agentsolve.payments.capabilities`
- `agentsolve.payments.stripe_payment_intents.create`
- `agentsolve.payments.account_credit_topups.create`
- `agentsolve.payments.account_credit_balance.get`
- `agentsolve.payments.authorities.create`
- `agentsolve.payments.authorities.list`
- `agentsolve.payments.authorities.revoke`
- `agentsolve.quotes.create`
- `agentsolve.jobs.create`
- `agentsolve.jobs.get`
- `agentsolve.jobs.cancel`
- `agentsolve.disputes.create`
- `agentsolve.jobs.reexecute`
- `agentsolve.uploads.create_handle`
- `agentsolve.billing.summary`
- `agentsolve.transparency.changes`
- `agentsolve.transparency.job`

## Polling-First Behavior

`agentsolve.jobs.create` returns `job_id`, `status`, `terminal`,
`recommended_poll_after_ms`, `poll_tool`, and `poll_url` where relevant. Use
`agentsolve.jobs.get` until terminal. Do not hide long-running solve work inside
one tool call.

## Error Envelope

MCP JSON-RPC failures place the stable V5 typed error envelope under
`error.data.agentsolve_error`. Read `code`, `message`, `retryable`,
`idempotency_relevant`, and redacted `details`.

## Idempotency

Creation tools expose caller-generated idempotency keys for quotes, jobs,
Stripe PaymentIntent preflight, disputes, and reexecution. Use a stable key for
retrying the same operation and a new key for a materially different payload.

## Scopes

Read-only discovery, schemas, menus, job polling, billing summary, and
transparency use `read`. Quote creation and upload handles use `quote:create`.
Job creation and quote-bound Stripe PaymentIntent preflight use `job:create`.
Cancellation, disputes, and reexecution use `job:write`.

Account-credit balance and payment-authority list operations require
`billing:read`. Account-credit top-ups and payment-authority create/revoke
operations require `billing:write`. The `mcp:*` wildcard is not a billing
wildcard and does not grant account-credit or payment-authority access by
itself.

Solver hints are backend-neutral execution modifiers. Use only published fields
such as `time_limit_seconds`, `relative_gap`, `absolute_gap`, and
`random_seed` when discovery says the class supports them.
