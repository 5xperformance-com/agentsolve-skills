# MCP Access

Contents: First Job Step By Step · Lifecycle Setup · Polling-First Behavior · Error Envelope

MCP is a thin access layer over the same canonical quote -> job -> poll
contract as REST. Each tool takes the REST request body as its `arguments`
and returns the REST response. Tools return quickly and do not wait for
compute completion. The class reference supplies the `input`; nothing else
needs opening on the way to a first result.

## First Job Step By Step

1. **Identity.** A connected, signed-in client skips this. Otherwise identity
   is the same HTTP operations REST uses: read
   `/.well-known/oauth-protected-resource` and `/auth.md`, then call
   `POST /v1/identity/bootstrap` with the managed-provider bearer
   ([reference-rest-access.md](reference-rest-access.md), step 1). MCP
   deliberately has no duplicate registration or bootstrap tool. Unclaimed
   payment by x402, the jurisdiction policy (US and UK only), and the
   current-policy-version check at registration are the same as over REST.

2. **Quote.** `agentsolve.quotes.create`, with the class reference's request
   as `arguments`: `idempotency_key`, `problem_type`,
   `problem_schema_version`, `input` and a `policy` (`max_price_usdc` at the
   least). Optional: `constraints` (`time_budget_ms`, at most 600000, and
   `solver_hints`) and `requested_ttl_seconds`. Nothing is charged. Keep
   `quote_token`, `candidates[]` (each with
   its `solver_admission_id`, engine name `solver_slot` and `price_locked_usdc`),
   `default_candidate_solver_admission_id`, `effective_solver_hints` and
   `payment_requirement.options[]`.

3. **Job.** `agentsolve.jobs.create`:

   ```json
   {"idempotency_key": "...", "quote_token": "...",
    "selected_algorithms": ["<solver_admission_id>"],
    "payment": {"rail": "account_credit",
                "payment_authority_id": "<pauth_... from the quote>"}}
   ```

   Routing has no default: send `selected_algorithms` (one id, or 2 to 10
   for a portfolio) or `auto_route: true`, never both. `payment` satisfies
   exactly one available option of the quote's `payment_requirement`. A
   claimed account with credit sends the authority id that the quote's
   `account_credit` option names in `instructions.payment_object`; when
   that option is unavailable, follow its `funding_guidance`
   ([reference-payment-rails.md](reference-payment-rails.md)). A newly
   registered agent pays by x402
   ([reference-payment-x402.md](reference-payment-x402.md)). If the quote's
   `effective_solver_hints` is not null (you sent `constraints`), send it
   verbatim as `solver_hints`.

   For a consumer the job also carries `consumer_start_acknowledgement`,
   set to the current terms version. Send it only after the consumer has
   expressly asked for the job to start at once and accepted that the right
   to cancel ends when the job is fully performed; permission to pay is not
   that consent. Without it the job is refused before payment as
   `INVALID_PAYLOAD` with `express_consumer_request_required`, and
   `details.extra.terms_version` names the version.

4. **Poll.** `agentsolve.jobs.get` with `{"job_id": "..."}`, waiting
   `recommended_poll_after_ms` between calls, until `terminal` is `true`.

5. **Read the result.** The terminal `agentsolve.jobs.get` result of a
   `SETTLED` job carries the answer inline in `output` and the receipt in
   `routing_receipt`; no other tool is needed. On the receipt read
   `established_guarantee` (`global_optimality`, `validity`,
   `infeasibility` or `unverified`), `attestation.claims` (a list of
   `{kind, source, payload}`; kind `solver_proved` is the engine's own
   proof, not the verifier's), `terminated_reason`
   (`completed_before_budget` or `budget_exhausted`), `price_locked_usdc`
   and `receipt_id`. A `REFUNDED` job explains itself in
   `terminal_diagnostic`
   ([reference-errors-and-retries.md](reference-errors-and-retries.md)).

## Lifecycle Setup

AgentSolve uses Streamable HTTP at `/mcp` with JSON-RPC POST requests. External MCP
clients should perform authenticated `initialize`, send
`notifications/initialized`, then use `tools/list` and `tools/call`; `ping`
is answered for liveness.

Lifecycle is connection setup only. AgentSolve does not issue
`MCP-Session-Id`, does not expose MCP resources or prompts, does not provide
server-push progress streams, and does not ship a stdio package. Use ordinary
job polling for product state. Official Streamable HTTP clients should send
`Accept: application/json, text/event-stream`; the server remains tolerant of
older client headers.

## Polling-First Behavior

`agentsolve.jobs.create` returns `job_id`, `status`, `terminal`,
`recommended_poll_after_ms`, `poll_tool`, and `poll_url` where relevant. Use
`agentsolve.jobs.get` until terminal. Do not hide long-running solve work inside
one tool call.

## Error Envelope

MCP JSON-RPC failures place the stable typed error envelope under
`error.data.agentsolve_error`. Read `code`, `message`, `retryable`,
`idempotency_relevant`, and redacted `details`.

A connected client already lists its tools. The full tool list, scopes,
idempotency rules and solver hints are in
[reference-mcp-tools.md](reference-mcp-tools.md).
