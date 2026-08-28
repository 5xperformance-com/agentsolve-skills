# MCP Access

MCP is a thin access layer over the same canonical quote -> job -> poll
contract as REST. Tools return quickly and do not wait for compute completion.

Identity discovery and bootstrap are the same HTTP operations used by REST:
read `/.well-known/oauth-protected-resource` and `/auth.md`, then call
`POST /v1/identity/bootstrap` with the managed-provider bearer. MCP deliberately
has no duplicate registration or bootstrap tool. The autonomous paid lane
remains disabled while its country allowlist is empty.

## Lifecycle Setup

Stage 0 uses Streamable HTTP at `/mcp` with JSON-RPC POST requests. External MCP
clients should perform authenticated `initialize`, send
`notifications/initialized`, then use `tools/list` and `tools/call`; `ping`
is answered for liveness.

Lifecycle is connection setup only. AgentSolve does not issue
`MCP-Session-Id`, does not expose MCP resources or prompts, does not provide
server-push progress streams, and does not ship a stdio package. Use ordinary
job polling for product state. Official Streamable HTTP clients should send
`Accept: application/json, text/event-stream`; the server remains tolerant of
older client headers.

## Tool Inventory

- `agentsolve.problems.list`
- `agentsolve.problems.get`
- `agentsolve.solvers.list`
- `agentsolve.schemas.get`
- `agentsolve.menus.get`
- `agentsolve.payments.capabilities`
- `agentsolve.payments.stripe_payment_intents.create`
- `agentsolve.payments.account_credit_topups.create`
- `agentsolve.payments.funding_links.create`
- `agentsolve.payments.account_credit_balance.get`
- `agentsolve.payments.authorities.create`
- `agentsolve.payments.authorities.list`
- `agentsolve.payments.authorities.revoke`
- `agentsolve.payments.faucet_programs.list`
- `agentsolve.quotes.create`
- `agentsolve.jobs.create`
- `agentsolve.jobs.get`
- `agentsolve.jobs.list`
- `agentsolve.jobs.cancel`
- `agentsolve.disputes.create`
- `agentsolve.jobs.reexecute`
- `agentsolve.uploads.create_handle`
- `agentsolve.billing.summary`
- `agentsolve.transparency.changes`
- `agentsolve.transparency.job`

Engine names are readable before buying: `agentsolve.solvers.list` is the
solver-catalog read path (there is no `GET /v1/solvers` REST route), and
every quote candidate carries `solver_slot` and `solver_version`.

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

Read-only discovery, schemas, menus, job polling, and transparency use `read`.
Quote creation uses `quote:create`. Upload-handle tools are disabled outside
local development and are not part of the current public workflow.
Job creation and quote-bound Stripe PaymentIntent preflight use `job:create`.
Cancellation, disputes, and reexecution use `job:write`.

Billing summary, account-credit balance, payment-authority list, and
faucet-program list operations require `billing:read`. Account-credit top-ups, funding-link minting
(`agentsolve.payments.funding_links.create` mints a signed funding-link URL a
human opens to buy account credit), and payment-authority create/revoke
operations require `billing:write`. The `mcp:*` wildcard is not a billing
wildcard and does not grant account-credit or payment-authority access by
itself.

Every static tool descriptor publishes its requirement as
`x-agentsolve-required-scope`; runtime `tools/list` still filters the catalog
to scopes held by the caller.

Solver hints are backend-neutral execution modifiers. Use only published fields
— `time_limit_seconds`, `mip_gap_relative`, `mip_gap_absolute`, `threads`,
and `random_seed` — when discovery says the class supports them. Hints bind
at quote time: send them under the quote's `constraints`, then resubmit the
quote's returned `effective_solver_hints` verbatim as the job's
`solver_hints`; any divergence is rejected with `QUOTE_HINTS_MISMATCH`.
