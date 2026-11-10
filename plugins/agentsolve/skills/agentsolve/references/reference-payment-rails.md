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

Portfolio (multi-member) jobs pay from account credit or trial credit only;
the Stripe rail rejects portfolios by design. A portfolio's total price is
the sum of its member prices and is checked against the quote's
`max_price_usdc` ceiling at job creation.

For account-credit flows, a human/account owner first buys credit through
`POST /v1/payments/account-credit/top-ups` and confirms the returned Stripe
PaymentIntent outside AgentSolve's card-data boundary; that top-up endpoint
requires `billing:write`. The simplest handoff is a funding link: call
`POST /v1/payments/account-credit/funding-links` (`billing:write`) and give
the returned URL to your human, who picks an amount (5.00 USD minimum) and
pays on AgentSolve's hosted top-up page — the card and SCA never touch the
agent. Account credit never expires.
An owner registered as a consumer must top up on that hosted page: it records
the consumer's express request that the credit be usable straight away and
their acknowledgement of the cancellation right, and a REST or MCP top-up
cannot carry either. A consumer's REST or MCP top-up is refused with `400` and
`consumer_acknowledgement_required`; send a consumer owner to a funding link.
After paying, the page offers a saveable confirmation of the purchase and the
Terms version it was made under. The account or owner then creates a
`PaymentAuthority` through `POST /v1/payments/authorities`, which also requires
`billing:write`. Agents may spend only by submitting `{"rail":"account_credit",
"payment_authority_id":"pauth_..."}` on `POST /v1/jobs`; they never submit lot
ids, top-up ids, credit amounts, or card/payment-method details. When a
quote's `account_credit` option is available, its
`instructions.payment_object` names the authority the quote validated for
this caller, class, and amount — submit exactly that id rather than picking
one from `GET /v1/payments/authorities`, which can choose an authority the
server will reject.

Authorities have a lifecycle even though credit does not: every authority
carries an `expires_at`, and an authority can be revoked. An expired or revoked authority removes the
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
like a card authorization. Businesses receive remedy credit. Consumers receive
USDC back to the paying wallet unless they expressly selected
`x402_refund_preference: "account_credit"` at registration. Do not make that
choice from spending permission alone. A pending USDC refund is unspendable;
`pending_refund_amount_usdc` reports it. AgentSolve pays the sending network
fee and returns it without undue delay, within 14 days of cancellation or
agreement that a refund is due. Contact `hello@agentsolve.io` with the
transaction hash if assistance is needed.
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

## Service area, cancellation and terms

AgentSolve serves the US and the UK. Card funding and account-credit top-ups
are available to billing countries `US` and `GB` only; credit already held
stays spendable. A consumer may cancel a card top-up within 14 days of paying:
email `hello@agentsolve.io` with the account and top-up ID, and the unspent
remainder is refunded to the card within 14 days; jobs run before cancelling
are paid from the top-up. A consumer may cancel a job by email before it is
fully performed, which usually takes minutes.

Before creating a consumer job, obtain the consumer's express request to
start immediately and acknowledgement that cancellation rights end on full
performance. Send the current terms version in `consumer_start_acknowledgement`
only with authority for both statements. The bundled tools accept that version
through `AGENTSOLVE_CONSUMER_START_TERMS_VERSION`; they never infer consent from
a payment budget or enable it automatically. A refusal with
`express_consumer_request_required` requires obtaining those instructions.

Every job's purchase confirmation is `GET /v1/jobs/{job_id}/confirmation`
(`read` scope), linked in the `AgentSolve-Confirmation` response header on job
creation and in the MCP job tool's result. It states the price, rail, Terms
version, seller and cancellation notice, and does not change after it is
issued.

A new registration's `POST /v1/identity/bootstrap` must name the current
version of each policy: `terms`, `privacy`, `x402_remedy` and `data_processing`.
`GET /auth.md` lists the current versions; any other version is refused with
`INVALID_PAYLOAD`, naming the policy and its current version.

Do not invent alternate payment rails. Billing read models live in
[reference-billing-and-quotes.md](reference-billing-and-quotes.md).
