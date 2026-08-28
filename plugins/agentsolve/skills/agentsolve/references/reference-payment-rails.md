# Payment Rails

Payment is one bounded step after an agent has described a problem, received
priced candidates, and chosen how to route the job. A quote may offer four
funding paths:

- Account-credit spend with `payment.rail=account_credit` and an explicit
  `payment_authority_id`.
- x402 exact-USDC payment for accountless autonomous agents.
- Stripe card authorization via a quote-bound PaymentIntent created by
  AgentSolve and confirmed through Stripe Elements.
- Trial-credit redemption with `payment.rail=trial_credit`.

Faucet-funded quotes are a trial-credit subsidy path, not a third rail.
Discover enrollment with `GET /v1/payments/faucet-programs` (`billing:read`;
MCP: `agentsolve.payments.faucet_programs.list`) — it lists every active
program the account can draw from, with remaining grant balance and per-job
ceiling — or read `payment_requirement.faucet_programs` on any quote. To use
one, request a fresh quote with `funding_mode: "faucet"` and the
`faucet_program_id`. When a quote returns
`payment_requirement.requires_payment=false` and
`instructions.method=job_create_without_payment`, create the job without
`payment`; AgentSolve synthesizes the trial-credit authorization internally.

This file reflects the implemented contract. Runtime discovery and the quote's
`available`, `currency`, and instructions fields decide what an agent may
submit. `stripe_spt` is review-gated, disabled by default, and appears only when
quote-level discovery marks it `available=true`.

For account-credit flows, a human/account owner first buys credit through
`POST /v1/payments/account-credit/top-ups` and confirms the returned Stripe
PaymentIntent outside AgentSolve's card-data boundary; that top-up endpoint
requires `billing:write`. The simplest handoff is a funding link: call
`POST /v1/payments/account-credit/funding-links` (`billing:write`) and give
the returned URL to your human, who picks an amount (10.00 USD minimum) and
pays on AgentSolve's hosted top-up page — the card and SCA never touch the
agent. The account or owner then creates a
`PaymentAuthority` through `POST /v1/payments/authorities`, which also requires
`billing:write`. Agents may spend only by submitting `{"rail":"account_credit",
"payment_authority_id":"pauth_..."}` on `POST /v1/jobs`; they never submit lot
ids, top-up ids, credit amounts, or card/payment-method details. When a
quote's `account_credit` option is available, its
`instructions.payment_object` names the authority the quote validated for
this caller, class, and amount — submit exactly that id rather than picking
one from `GET /v1/payments/authorities`, which can choose an authority the
server will reject.

Authorities have a lifecycle: every authority carries an `expires_at`, and an
authority can be revoked. An expired or revoked authority removes the
account-credit option from quotes even when credit is available; the quote
then reports `payment_authority_expired` or `payment_authority_revoked` on
the option and names the recovery in `funding_guidance`. The self-heal is one
step for a caller holding `billing:write`: create a fresh authority with
`POST /v1/payments/authorities`, then request a fresh quote — the credit
balance itself is untouched. `GET /v1/payments/authorities` lists every
authority with its status and expiry. If a quote
marks `account_credit` unavailable, use another available rail or follow the
requirement's `funding_guidance` (mint a funding link, have the owner fund and
authorize, then request a fresh quote).

For x402 flows, read the quote's `payment_requirement` and use an available
`x402` option exactly as published. The `payment_payload` submitted on
`POST /v1/jobs` must be the decoded x402 `X-PAYMENT` JSON payload and must
match AgentSolve's quote-derived requirements for scheme, network, asset,
amount, payee, timeout, and single-use proof. Do not reuse an x402 payload on
another quote or job; replayed proofs are rejected.

x402 settles USDC before job persistence and execution; it cannot be voided
like a card authorization. A failed or refunded x402 job is remedied with
spendable account credit; the on-chain transfer itself is not reversed.
Whether x402 is available for a given quote is a quote fact: read the
quote's payment options and use what the quote offers.

For Stripe card flows, agents should never collect raw card data. They should
read the quote's `payment_requirement`, call
`POST /v1/payments/stripe/payment-intents` using the quote token and the same
job idempotency key later used on `POST /v1/jobs`, confirm the returned
PaymentIntent through Stripe, and submit the resulting `payment_intent_id` when
creating the job. Only do this when the quote marks the Stripe option
`available=true`; low-value quotes below the direct Stripe rail minimum will
mark Stripe unavailable and the preflight endpoint will reject them. The
implemented third-party payout service targets Stripe Connect Custom; agents do
not choose provider account types. Current first-party jobs record provider
payout `NOT_APPLICABLE`.

For review-gated Stripe SPT flows, agents must follow the exact quote-level
`stripe_spt` option and submit only the request-only `shared_payment_token`
with the quote's `payment_requirement_id`, exact USD amount, and optional AP2
mandate hash. AgentSolve persists only a keyed SPT fingerprint and Stripe
PaymentIntent reconciliation ids. Do not submit raw card data, direct ACP
payment payloads, AP2 plaintext payment credentials, or Stripe `client_secret`.
Stripe SPT is currently a US-seller product (registry region `US`); a UK
AgentSolve seller profile keeps this option unavailable unless Stripe explicitly
approves UK seller access or AgentSolve uses an eligible US seller profile.

For trial credits, pass the redemption material through the documented
trial-credit fields and preserve the quote/job idempotency keys. Trial-credit
tax and fee treatment is visible in `receipt.v5`.

Do not invent alternate payment rails. Billing read models live in
[reference-billing-and-quotes.md](reference-billing-and-quotes.md).
