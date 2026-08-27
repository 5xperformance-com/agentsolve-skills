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
It also returns the exact-input
`instance_descriptor`, a top-level `estimate_basis`, and candidate
`evidence_scope_state` values. `catalog_projection` is an estimate, not a
measured latency or quality guarantee. Callers that require measured scope can
set `policy.minimum_evidence_state` to `qualification_only` or
`production_observed`; the default remains `declared_only`.
The quote also returns a quote-bound
`payment_requirement` with ranked payment options. `default_rail` names a
satisfiable option or is null; when null, read `funding_guidance`.

Use `/v1/billing/summary` and `/v1/billing/charges` with `billing:read` for
billing read models.
Receipt `receipt.v5` is current; older receipt versions are immutable legacy.

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
