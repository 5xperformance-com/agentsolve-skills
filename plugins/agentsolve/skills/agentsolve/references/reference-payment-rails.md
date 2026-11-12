# Payment Rails

Contents: Account Credit · Payment Authorities · Portfolios · Card Through Stripe · Trial Credit And Faucet Programs · Stripe SPT · Consumers · Purchase Confirmation

A quote may offer four funding paths. A newly registered agent has the
second; the other three need a claimed account:

- Account-credit spend with `payment.rail=account_credit` and an explicit
  `payment_authority_id`.
- x402 exact-USDC payment from the agent's own wallet:
  [reference-payment-x402.md](reference-payment-x402.md).
- Stripe card authorization via a quote-bound PaymentIntent created by
  AgentSolve and confirmed through Stripe Elements.
- Trial-credit redemption with `payment.rail=trial_credit`.

The quote's `payment_requirement` decides what a job may use: read each
option's `available`, `currency` and `instructions`, and satisfy exactly
one. Do not invent other rails. Billing read models are in
[reference-billing-and-quotes.md](reference-billing-and-quotes.md).

A person claims the agent by emailing `hello@agentsolve.io`; the claimed
credential carries `billing:write`. AgentSolve serves the US and the UK. Card
funding and account-credit top-ups are available to billing countries `US`
and `GB` only; credit already held stays spendable.

## Account Credit

The owner buys credit, then the agent spends it through a payment authority.

- Simplest: mint a funding link with
  `POST /v1/payments/account-credit/funding-links` (`billing:write`; MCP
  `agentsolve.payments.funding_links.create`) and give the URL to your human.
  They pick an amount (5.00 USD minimum) and pay on AgentSolve's hosted
  top-up page; the card and SCA never touch the agent.
- Or call `POST /v1/payments/account-credit/top-ups` (`billing:write`) and
  confirm the returned Stripe PaymentIntent outside AgentSolve's card-data
  boundary.
- Account credit never expires. Top-ups are limited to 250 USD in any 24
  hours and 1,000 USD in any 30 days, and an account holds at most 250 USD
  of credit.

Spend by sending
`"payment": {"rail": "account_credit", "payment_authority_id": "pauth_..."}`
on job creation. Never send lot ids, top-up ids, credit amounts or card
details. When a quote's `account_credit` option is available, its
`instructions.payment_object` names the authority the quote validated for
this caller, class and amount. Submit exactly that id rather than picking
one from `GET /v1/payments/authorities`, which can choose an authority the
server will reject.

## Payment Authorities

An authority is the owner's standing permission for the agent to spend
credit. Create one with `POST /v1/payments/authorities` (`billing:write`;
MCP `agentsolve.payments.authorities.create`):

```json
{
  "max_amount_per_job_usdc": "1.00",
  "daily_cap_usdc": "5.00",
  "monthly_cap_usdc": "20.00",
  "max_outstanding_reserved_usdc": "5.00",
  "expires_at": "2027-01-31T00:00:00Z",
  "allowed_problem_classes": ["4.2.scheduling.jssp"]
}
```

`allowed_problem_classes` is optional; omit it to allow every class.

Authorities have a lifecycle even though credit does not: every authority
carries an `expires_at`, and an authority can be revoked. An expired or
revoked authority removes the account-credit option from quotes even when
credit is available; the quote then reports `payment_authority_expired` or
`payment_authority_revoked` on the option and names the recovery in
`funding_guidance`. The self-heal is one step for a caller holding
`billing:write`: create a fresh authority, then request a fresh quote. The
credit balance itself is untouched. `GET /v1/payments/authorities` lists
every authority with its status and expiry. If a quote marks
`account_credit` unavailable, use another available rail or follow the
requirement's `funding_guidance` (mint a funding link, have the owner fund
and authorize, then request a fresh quote).

## Portfolios

A portfolio (2 to 10 solvers on one job) pays from account credit or trial
credit only: the Stripe rail rejects portfolios by design, and x402 pays for
one solver per job. Its total
price is the sum of its member prices and is checked against the quote's
`max_price_usdc` ceiling at job creation.

## Card Through Stripe

Never collect raw card data. Read the quote's `payment_requirement`, call
`POST /v1/payments/stripe/payment-intents` with the quote token and the same
job idempotency key later used on `POST /v1/jobs`, confirm the returned
PaymentIntent through Stripe Elements, and submit the resulting
`payment_intent_id` when creating the job. Only do this when the quote marks
the Stripe option `available=true`: a quote below the direct Stripe minimum
of 0.50 USD marks Stripe unavailable and the preflight endpoint rejects it,
and a card then pays by topping up account credit. The preflight also needs
a claimed credential. The implemented third-party payout service targets
Stripe Connect Custom; agents do not choose provider account types. Current
first-party jobs record provider payout `NOT_APPLICABLE`.

## Trial Credit And Faucet Programs

Redeem trial credit with `payment.rail=trial_credit`: pass the redemption
material through the documented trial-credit fields and preserve the quote
and job idempotency keys. Trial-credit tax and fee treatment is visible in
`receipt.v6`.

Faucet-funded quotes are a kind of trial credit, not a rail of their own.
AgentSolve grants trial credit and faucet enrollments at its discretion;
none is offered by default, and an unclaimed agent cannot use one. Discover
enrollment with `GET /v1/payments/faucet-programs` (`billing:read`; MCP
`agentsolve.payments.faucet_programs.list`), which lists every active
program the account can draw from, with remaining grant balance and per-job
ceiling, or read `payment_requirement.faucet_programs` on any quote. To use
one, request a fresh quote with `funding_mode: "faucet"` and the
`faucet_program_id`. When a quote returns
`payment_requirement.requires_payment=false` and
`instructions.method=job_create_without_payment`, create the job without
`payment`; AgentSolve synthesizes the trial-credit authorization internally.

## Stripe SPT

`stripe_spt` is review-gated, disabled by default, and appears only when
quote-level discovery marks it `available=true`. Follow the exact
quote-level `stripe_spt` option and submit only the request-only
`shared_payment_token` with the quote's `payment_requirement_id`, exact USD
amount, and optional AP2 mandate hash. AgentSolve persists only a keyed SPT
fingerprint and Stripe PaymentIntent reconciliation ids. Do not submit raw
card data, direct ACP payment payloads, AP2 plaintext payment credentials,
or Stripe `client_secret`. Stripe SPT is currently a US-seller product
(registry region `US`); a UK AgentSolve seller profile keeps this option
unavailable unless Stripe explicitly approves UK seller access or AgentSolve
uses an eligible US seller profile.

## Consumers

An owner registered as a consumer must top up on the hosted funding-link
page: it records the consumer's express request that the credit be usable
straight away and their acknowledgement of the cancellation right, and a
REST or MCP top-up cannot carry either. A consumer's REST or MCP top-up is
refused with `400` and `consumer_acknowledgement_required`; send a consumer
owner to a funding link. After paying, the page offers a saveable
confirmation of the purchase and the Terms version it was made under.

A consumer may cancel a card top-up within 14 days of paying: email
`hello@agentsolve.io` with the account and top-up ID, and the unspent
remainder is refunded to the card within 14 days; jobs run before cancelling
are paid from the top-up. A consumer may cancel a job by email before it is
fully performed, which usually takes minutes.

Before creating a consumer job, obtain the consumer's express request to
start immediately and acknowledgement that cancellation rights end on full
performance. Send the current terms version in
`consumer_start_acknowledgement` only with authority for both statements.
The bundled tools accept that version through
`AGENTSOLVE_CONSUMER_START_TERMS_VERSION`; they never infer consent from a
payment budget or enable it automatically. A refusal with
`express_consumer_request_required` requires obtaining those instructions.

## Purchase Confirmation

Every job's purchase confirmation is `GET /v1/jobs/{job_id}/confirmation`
(`read` scope), linked in the `AgentSolve-Confirmation` response header on
job creation and in the MCP job tool's result. It states the price, rail,
Terms version, seller and cancellation notice, and does not change after it
is issued.
