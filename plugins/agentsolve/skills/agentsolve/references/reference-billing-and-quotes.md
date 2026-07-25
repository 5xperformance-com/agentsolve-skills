# Billing And Quotes

AgentSolve is quote-first. Invalid input is rejected before charging; accepted
jobs bind economics to the quote.

## Quote Flow

Create a quote with canonical `problem_type`, `problem_schema_version`, input,
policy, constraints, and idempotency key. The quote returns a token, expiry,
locked price ceiling, selected option, policy eliminations, warning blocks, and
any `solver_hints_hash`. The quote also returns a quote-bound
`payment_requirement` with ranked payment options.

Use `/v1/billing/summary` and `/v1/billing/charges` for billing read models.
Receipt `receipt.v3` is the current receipt schema; `receipt.v2` is immutable
legacy.

## Funding Paths

- Account-credit spend with `payment.rail=account_credit` and an explicit
  `payment_authority_id` created by a billing-scoped owner.
- x402 exact-USDC payment with the decoded quote-derived x402 payload submitted
  on `POST /v1/jobs`.
- Stripe card authorization via `POST /v1/payments/stripe/payment-intents`,
  followed by Stripe-side confirmation and job creation with the confirmed
  `payment_intent_id`.
- Trial-credit redemption with `payment.rail=trial_credit`.
- Faucet-funded quotes, when explicitly requested and approved, return
  `payment_requirement.requires_payment=false`; create the job without a
  `payment` object and rely on the receipt's trial-credit code hash for audit.

Every job-create request must also choose a routing mode explicitly:
`auto_route: true` for platform-selected routing, one id in
`selected_algorithms` for Mode 1, or 2 to 10 ids for portfolio mode.

Review-gated payment-overhaul rails are intentionally non-executable in this
active adoption reference until their payment-evidence contracts are updated and
activated. If an unavailable option appears in `payment_requirement.options`,
do not submit it to `POST /v1/jobs`.

Tax and rail fee fields are interpreted through the settled receipt. Trial
credit receipts expose `subsidy_amount_usdc`, preserve economic lineage, and
do not imply a second caller charge.
