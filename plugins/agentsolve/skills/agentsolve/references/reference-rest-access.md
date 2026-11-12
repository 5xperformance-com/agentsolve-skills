# REST Access

Contents: First Job Step By Step · Identity And Renewal

Every call of a job over REST. The class reference supplies the `input`;
nothing else needs opening on the way to a first result. The service address
is `https://api.agentsolve.io`. Bodies are JSON, and the credential travels
as `Authorization: Bearer <token>`. MCP makes the same calls as tools
([reference-mcp-access.md](reference-mcp-access.md)).

## First Job Step By Step

1. **Credential.** Follow `GET /auth.md`: register at the issuer it names,
   naming your client in a `User-Agent` header (the issuer refuses a bare
   HTTP-library default), and exchange the returned assertion for a bearer,
   which lasts about a day. Do not guess registration or token endpoints:
   take them from `GET /.well-known/oauth-protected-resource` and the
   authorization metadata it advertises. Then call bootstrap once:

   ```json
   POST /v1/identity/bootstrap
   {"principal_type": "business", "billing_country": "GB",
    "terms_version": "...", "privacy_version": "...",
    "x402_remedy_version": "...", "data_processing_version": "..."}
   ```

   `principal_type` is `business` or `consumer`. The four versions are the
   current ones `/auth.md` lists; any other is refused with
   `INVALID_PAYLOAD`, naming the policy and its current version. A US
   billing address also needs `billing_state` and `billing_postal_code`.
   AgentSolve serves the billing countries GB and US only. Any other billing
   country is refused at bootstrap and gets no quote (403).

2. **Quote.** `POST /v1/quotes` with the class reference's request:
   `idempotency_key`, `problem_type`, `problem_schema_version`, `input` and
   a `policy` (`max_price_usdc` at the least). Optional:
   `constraints` (`time_budget_ms`, `solver_hints`) and
   `requested_ttl_seconds` (60 at the least). Nothing is charged. Keep
   `quote_token`, `quote_expires_at`, `candidates[]` (each with its
   `solver_admission_id`, engine name `solver_slot` and `price_locked_usdc`), `default_candidate_solver_admission_id`,
   `effective_solver_hints` and `payment_requirement.options[]`.

3. **Job.** `POST /v1/jobs`:

   ```json
   {"idempotency_key": "...", "quote_token": "...",
    "selected_algorithms": ["<solver_admission_id>"],
    "payment": {"rail": "..."}}
   ```

   There is no implicit routing default. Include exactly one of:
   `selected_algorithms` with one id for one agent-selected solver,
   `selected_algorithms` with 2 to 10 ids for a portfolio, or
   `auto_route: true` for the platform's deterministic choice. Auto-route
   runs the class's catalog default when it is an eligible candidate; only
   when it is not are the others ranked by trust, then quality, then
   latency, then price.
   `payment` satisfies exactly one available option of the quote's
   `payment_requirement`: a newly registered agent pays by x402
   ([reference-payment-x402.md](reference-payment-x402.md)); a claimed
   account has more ([reference-payment-rails.md](reference-payment-rails.md)).
   If `requires_payment=false`, omit `payment`. If the quote bound solver
   hints (anything sent under `constraints`, including `time_budget_ms`),
   its `effective_solver_hints` is not null: send it verbatim as the job's
   `solver_hints`;
   any divergence is rejected with `QUOTE_HINTS_MISMATCH`. The response
   carries `job_id`, `status`, `terminal` and `recommended_poll_after_ms`.

   For a consumer (`principal_type: consumer`) the job also carries
   `consumer_start_acknowledgement`, set to the current terms version. Send
   it only after the consumer has expressly asked for the job to start at
   once and accepted that the right to cancel ends when the job is fully
   performed; permission to pay is not that consent. Without it the job is
   refused before payment as `INVALID_PAYLOAD` with
   `express_consumer_request_required`, and `details.extra.terms_version`
   names the version.

4. **Poll.** `GET /v1/jobs/{job_id}`, waiting `recommended_poll_after_ms`
   between reads, until `terminal` is `true`. There is no event stream at
   launch: polling is the only completion mechanism, and the contract loses
   nothing by it. Terminal states are `SETTLED`, `REFUNDED`, `DISPUTED` and
   `SUPERSEDED`. A portfolio's rules are in
   [reference-polling-and-backoff.md](reference-polling-and-backoff.md).

5. **Read the result.** A `SETTLED` job read carries the answer inline in
   `output` (the same bytes as `GET /v1/jobs/{job_id}/output`; pass
   `include_output=false` to leave it out while polling a large job) and
   the receipt in `routing_receipt`. On the receipt read:
   - `established_guarantee`, what the verifier established:
     `global_optimality`, `validity` (checked valid, not proved optimal),
     `infeasibility` or `unverified`;
   - `attestation.claims`, a list of `{kind, source, payload}`, where kind
     `solver_proved` is the engine's own proof and not the verifier's;
   - `terminated_reason`: `completed_before_budget` or `budget_exhausted`;
   - `price_locked_usdc` and `receipt_id`.

   A `REFUNDED` job explains itself in `terminal_diagnostic`. Any refusal on
   the way is one error envelope:
   [reference-errors-and-retries.md](reference-errors-and-retries.md).

## Identity And Renewal

REST and MCP clients share the HTTP identity control plane; MCP has no
separate bootstrap tool. Bootstrap returns stable AgentSolve subject,
account, and logical credential IDs. Exact replay returns those IDs without
redisplaying the one-time migration-recovery code; changed declarations fail
with `IDENTITY_BOOTSTRAP_CONFLICT`. To renew, exchange the assertion again
and repeat the same bootstrap body; until then the new bearer answers 401.

An unclaimed (autonomous) identity pays for each job with exact x402 USDC
from its own wallet, 0.01 to 5.00 USDC a job; claiming adds card payments
and funded account credit and is never required to buy. It holds one unpaid
quote at a time: until that quote is paid or expires, the next quote answers
429 `RATE_LIMITED`. Ask for a short quote with `requested_ttl_seconds` when
comparing rather than buying. A claim is requested by emailing
`hello@agentsolve.io`; staff complete it. At launch a claimed agent's key
lasts about a day and a fresh key takes a fresh claim.

Scopes, idempotency rules, the full endpoint list and body limits are in
[reference-rest-endpoints.md](reference-rest-endpoints.md).
