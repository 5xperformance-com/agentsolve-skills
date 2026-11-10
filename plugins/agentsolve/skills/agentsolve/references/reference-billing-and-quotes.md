# Billing And Quotes

AgentSolve is quote-first. Invalid input is rejected before charging; accepted
jobs bind economics to the quote.

## Quote Flow

Create a quote with canonical `problem_type`, `problem_schema_version`, input,
policy, constraints, and idempotency key. The quote returns a token, expiry,
locked price ceiling, selected option, policy eliminations, warning blocks, and
any `solver_hints_hash`. When the quote bound hints (anything sent under
`constraints`, including `time_budget_ms`), the response's
`effective_solver_hints` is the exact object the job must resubmit as
`solver_hints`; divergence is rejected with `QUOTE_HINTS_MISMATCH`.
The two layers use different names and units for the same bound:
`constraints.time_budget_ms` (milliseconds, quote-side) folds into the
hint `time_limit_seconds` (seconds, job-side) — the quote does the
conversion; never hand-build the hint. A larger `time_budget_ms` raises the
quote price: every second beyond the 120-second included budget is priced at
the published extended-time rate (0.35 USDC per hour, rounded up to the
cent) and shown as `price_components.extended_time_allowance_usdc`. The
purchasable budget is capped at ten minutes (600 seconds) at launch
capacity: a quote asking for more, through `constraints.time_budget_ms`,
`constraints.solver_hints.time_limit_seconds` or the input's
`metadata.time_limit_seconds`, is refused with `422 INVALID_PAYLOAD`,
`details.field_name` naming the field and
`details.extra.max_purchasable_solve_budget_seconds` the ceiling; ask for
at most that. Whether more time is worth buying is a question for the
receipts, not the price.
It also returns the exact-input
`instance_descriptor`, a top-level `estimate_basis`, and candidate
`evidence_scope_state` values. `catalog_projection` is an estimate, not a
measured latency or quality guarantee. A candidate with a verified
qualification run in the quoted size region carries `qualification_only`
evidence: `qualification_observation_count` counts the runs in that region,
`tested_size_regions` lists every region the solver qualified in, and
`tested_feature_envelope` bounds the tested case. A job intent no
qualification run measured, named in the summary's `job_intent`, is outside
the measured evidence. A region with no qualification run, such as TSP `XS`,
stays `declared_only`.
`production_observation_count` is 0 on quotes. Callers that require measured
scope can set `policy.minimum_evidence_state` to `qualification_only` or
`production_observed`; the default remains `declared_only`. Each candidate the
filter drops appears in `policy_eliminations` as `solver_filtered`, with detail
`"<solver_slot>: minimum_evidence_state <state>"`. When it drops every
candidate, the quote fails with `NO_ELIGIBLE_SOLVER` and the rejection reason
names the filter and the number of solvers dropped.
The quote also returns a quote-bound
`payment_requirement` with ranked payment options. `default_rail` names a
satisfiable option or is null; when null, read `funding_guidance`.

Use `/v1/billing/summary` and `/v1/billing/charges` with `billing:read` for
billing read models.
Receipt `receipt.v6` is current; older receipt versions are immutable legacy.

## Funding Paths

- Account-credit spend with `payment.rail=account_credit` and an explicit
  `payment_authority_id` created by a billing-scoped owner.
- x402 exact-USDC payment with the decoded quote-derived x402 payload submitted
  on `POST /v1/jobs`.
- Stripe card authorization via `POST /v1/payments/stripe/payment-intents`,
  using `job:create`, followed by Stripe-side confirmation and job creation
  with the confirmed `payment_intent_id`.
- Trial-credit redemption with `payment.rail=trial_credit`.
- Faucet-funded quotes, when explicitly requested and approved, return
  `payment_requirement.requires_payment=false`; create the job without a
  `payment` object and rely on the receipt's trial-credit code hash for audit.
  Enrollment is discoverable: `GET /v1/payments/faucet-programs` lists active
  programs for the calling account, and non-faucet quotes advertise them in
  `payment_requirement.faucet_programs`.

When funding fails, read the quote's `funding_guidance` before retrying: it
names caller-actionable recoveries such as re-creating an expired or revoked
spend authority (`POST /v1/payments/authorities`, `billing:write`) or
re-quoting with `funding_mode="faucet"` against an advertised enrollment.

Every job-create request must also choose a routing mode explicitly: one id
in `selected_algorithms` for Mode 1, 2 to 10 ids for portfolio mode, or
`auto_route: true` for the platform's deterministic catalog-default
selection.

Review-gated payment-overhaul rails are intentionally non-executable in this
active adoption reference until their payment-evidence contracts are updated and
activated. If an unavailable option appears in `payment_requirement.options`,
do not submit it to `POST /v1/jobs`.

Tax and rail fee fields are interpreted through the settled receipt. Trial
credit receipts expose `subsidy_amount_usdc`, preserve economic lineage, and
do not imply a second caller charge.
