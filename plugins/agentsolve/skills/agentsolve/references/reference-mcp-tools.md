# MCP Tools, Scopes And Hints

Contents: Tool Inventory · Idempotency · Scopes · Feedback Tools

Lookup material for calls beyond a first job, which
[reference-mcp-access.md](reference-mcp-access.md) walks through.

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
- `agentsolve.feature_requests.list`
- `agentsolve.feature_requests.get`
- `agentsolve.feature_requests.list_mine`
- `agentsolve.feature_requests.get_mine`
- `agentsolve.feature_requests.create`
- `agentsolve.feature_requests.vote`
- `agentsolve.feature_requests.unvote`
- `agentsolve.bug_reports.create`
- `agentsolve.bug_reports.list`
- `agentsolve.bug_reports.get`

Engine names are readable before buying: `agentsolve.solvers.list` is the
solver-catalog read path (over REST the same list is
`GET /v1/problems/{problem_type}/solvers`), and every quote candidate carries
`solver_slot` and `solver_version`.

## Idempotency

Creation tools expose caller-generated idempotency keys for quotes, jobs,
Stripe PaymentIntent preflight, account-credit top-ups, disputes, reexecution,
feature requests, and bug reports. Use a stable key for retrying the same
operation and a new key for a materially different payload.

## Scopes

Read-only discovery, schemas, menus, job polling, transparency, and the
feature-request and bug-report reads use `read`.
Quote creation uses `quote:create`. The upload-handle tool is available and
uses the same scope; see [large inputs](reference-large-inputs.md) for its
limits.
Job creation and quote-bound Stripe PaymentIntent preflight use `job:create`.
Cancellation, disputes, reexecution, feature-request and bug-report
submission, and feature-request voting use `job:write`.

Billing summary, account-credit balance, payment-authority list, and
faucet-program list operations require `billing:read`. Account-credit top-ups (refused for a consumer owner with
`consumer_acknowledgement_required`; mint a funding link instead), funding-link minting
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
at quote time: send them as `constraints.solver_hints`, then resubmit the
quote's returned `effective_solver_hints` verbatim as the job's
`solver_hints`; any divergence is rejected with `QUOTE_HINTS_MISMATCH`.

## Feedback Tools

The feedback tools mirror the REST feature-request and bug-report operations
and spend the same request allowances. `agentsolve.feature_requests.create`
and `agentsolve.bug_reports.create` submit for operator screening. The new item
is private and visible to you through `agentsolve.feature_requests.list_mine`,
`agentsolve.feature_requests.get_mine` or the bug-report reads. A feature
request stays private until an operator publishes it, and bug reports stay
private in every status. `agentsolve.feature_requests.list` and
`agentsolve.feature_requests.get` return only published requests even though
the call is authenticated; search with `list` before filing. Never put
secrets, payloads or personal data in a title or body. Every call to a feedback
tool, including an invalid or refused one, spends its kind's request allowance.
The lifecycle, statuses and limits are in
[feedback and bug reports](reference-feedback-and-bug-reports.md).
