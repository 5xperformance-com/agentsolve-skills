# Payment Rails

Stage 0 agent-facing payment guidance has four funding paths:

- Account-credit spend with `payment.rail=account_credit` and an explicit
  `payment_authority_id`.
- x402 exact-USDC payment for accountless autonomous agents.
- Stripe card authorization via a quote-bound PaymentIntent created by
  AgentSolve and confirmed through Stripe Elements.
- Trial-credit redemption with `payment.rail=trial_credit`.

Faucet-funded quotes are a trial-credit subsidy path, not a third rail. When a
quote returns `payment_requirement.requires_payment=false` and
`instructions.method=job_create_without_payment`, create the job without
`payment`; AgentSolve synthesizes the trial-credit authorization internally.

This file reflects the active public contract. `stripe_spt` is review-gated,
disabled by default, and appears only when quote-level discovery marks it
`available=true`; do not present it as an ordinary launch rail.

For account-credit flows, a human/account owner first buys credit through
`POST /v1/payments/account-credit/top-ups` and confirms the returned Stripe
PaymentIntent outside AgentSolve's card-data boundary; that top-up endpoint
requires `billing:write`. The account or owner then creates a
`PaymentAuthority` through `POST /v1/payments/authorities`, which also requires
`billing:write`. Agents may spend only by submitting `{"rail":"account_credit",
"payment_authority_id":"pauth_..."}` on `POST /v1/jobs`; they never submit lot
ids, top-up ids, credit amounts, or card/payment-method details. If a quote
marks `account_credit` unavailable, use another available rail or ask the owner
to top up/create authority.

For x402 flows, read the quote's `payment_requirement` and use the available
`x402` option exactly as published. The `payment_payload` submitted on
`POST /v1/jobs` must be the decoded x402 `X-PAYMENT` JSON payload and must
match AgentSolve's quote-derived requirements for scheme, network, asset,
amount, payee, timeout, and single-use proof. Do not reuse an x402 payload on
another quote or job; replayed proofs are rejected.

For Stripe card flows, agents should never collect raw card data. They should
read the quote's `payment_requirement`, call
`POST /v1/payments/stripe/payment-intents` using the quote token and the same
job idempotency key later used on `POST /v1/jobs`, confirm the returned
PaymentIntent through Stripe, and submit the resulting `payment_intent_id` when
creating the job. Only do this when the quote marks the Stripe option
`available=true`; low-value quotes below the direct Stripe rail minimum will
mark Stripe unavailable and the preflight endpoint will reject them. Provider
payouts use the platform's Stripe Connect Custom setup; agents do not choose
provider account types.

For review-gated Stripe SPT flows, agents must follow the exact quote-level
`stripe_spt` option and submit only the request-only `shared_payment_token`
with the quote's `payment_requirement_id`, exact USD amount, and optional AP2
mandate hash. AgentSolve persists only a keyed SPT fingerprint and Stripe
PaymentIntent reconciliation ids. Do not submit raw card data, direct ACP
payment payloads, AP2 plaintext payment credentials, or Stripe `client_secret`.
Stripe SPT is currently US-only for the agent/customer/seller ecosystem; a UK
AgentSolve seller profile keeps this option unavailable unless Stripe explicitly
approves UK seller access or AgentSolve uses an eligible US seller profile.

For trial credits, pass the redemption material through the documented
trial-credit fields and preserve the quote/job idempotency keys. Trial-credit
tax and fee treatment is visible in `receipt.v3`.

Do not invent alternate payment rails. Billing read models live in
[reference-billing-and-quotes.md](reference-billing-and-quotes.md).
