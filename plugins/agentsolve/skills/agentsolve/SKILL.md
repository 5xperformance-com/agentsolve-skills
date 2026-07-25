---
name: agentsolve
description: Use when selecting an AgentSolve Stage 0 class or driving the canonical quote -> job -> poll flow without solver-native or engine-internal payloads.
---

# AgentSolve

Use this skill for AgentSolve Stage 0 adoption work: classify the request,
choose the canonical problem type, draft against the active canonical schema,
create a quote, create a job, and poll the job to a terminal state.

## Getting Started

Happy path for a first integration:

1. Read [references/class-selection.md](references/class-selection.md) and
   choose one of the six Stage 0 launch classes below.
2. Create `POST /v1/quotes` with canonical input, a stable idempotency key, and
   a policy that fits the buyer's price/latency needs.
3. Read the quote response's `candidates` and `payment_requirement`.
4. Choose an explicit routing mode for `POST /v1/jobs`:
   - fastest first run: pass `auto_route: true`
   - agent-chosen solver: pass `selected_algorithms: ["<solver_admission_id>"]`
   - portfolio comparison: pass `selected_algorithms` with 2 to 10 ids
5. Satisfy exactly one available payment option from `payment_requirement`.
   Omit `payment` only when `payment_requirement.requires_payment=false`.
6. Poll `GET /v1/jobs/{job_id}` until `SETTLED`, `REFUNDED`, `DISPUTED`, or
   `SUPERSEDED`, then read output and receipt together.

Start with [references/class-selection.md](references/class-selection.md) when
the request is ambiguous, especially for routing, scheduling, inventory,
integer allocation, or any wording that sounds like a deferred variant.

Funding is quote-bound. Active Stage 0 rails are account credit with an
explicit `PaymentAuthority`, x402 exact-USDC payment, Stripe PaymentIntent
preflight plus Stripe-side confirmation, and trial-credit redemption. Follow
the quote-level `available` flag for every rail; see
[references/reference-billing-and-quotes.md](references/reference-billing-and-quotes.md)
and [references/reference-payment-rails.md](references/reference-payment-rails.md).
`stripe_spt` remains review-gated and must not be used unless a quote marks it
`available=true`.

Stage 0 launch classes:

- `1.1.tsp`
- `1.2.vrp.cvrp`
- `2.1.lp`
- `2.2.milp`
- `3.1.newsvendor`
- `4.1.scheduling.rcpsp`

Scheduling adjacency:

- `4.2.scheduling.jssp` is planned only.

Canonical flow:

1. Classify the request from the customer phrasing and boundary map.
2. Confirm the active problem type and schema versions from discovery.
3. Draft the provider-neutral canonical input only.
4. Create the quote, keeping the same problem type and input schema version.
5. Create the job from the accepted quote.
6. Poll until terminal, then read the output and receipt together.

Non-guarantees to preserve in agent-facing answers:

- No global optimality claim unless the returned evidence certifies it.
- No claim that Stage 0 covers every optimization or inference domain.
- No provider-hosted privacy guarantee or enclave-backed execution claim.
- No decentralization or governance-by-stake claim.
- No zero-variance latency or price forecast claim.

Guardrails:

- Use canonical AgentSolve schemas only.
- Do not describe planned scheduling adjacency as launch execution.
- Do not infer support for deferred variants from nearby launch classes.
- Do not expose internal engine surfaces, internal error shapes, or solver
  implementation payloads.
- Keep formulation detail in one-hop `references/*` files as they are authored.

Problem-type references:

- [references/problem-type-tsp.md](references/problem-type-tsp.md)
- [references/problem-type-vrp-cvrp.md](references/problem-type-vrp-cvrp.md)
- [references/problem-type-newsvendor.md](references/problem-type-newsvendor.md)
- [references/problem-type-lp.md](references/problem-type-lp.md)
- [references/problem-type-milp.md](references/problem-type-milp.md)
- [references/problem-type-rcpsp.md](references/problem-type-rcpsp.md)

Method references:

- [references/method-combinatorial-routing.md](references/method-combinatorial-routing.md)
- [references/method-linear-programming.md](references/method-linear-programming.md)
- [references/method-mixed-integer-linear-programming.md](references/method-mixed-integer-linear-programming.md)
- [references/method-stochastic-newsvendor.md](references/method-stochastic-newsvendor.md)
- [references/method-constraint-programming-scheduling.md](references/method-constraint-programming-scheduling.md)
- [references/formulation-patterns.md](references/formulation-patterns.md)
- [references/infeasibility-diagnostics.md](references/infeasibility-diagnostics.md)
- [references/reference-verification-and-certificates.md](references/reference-verification-and-certificates.md)

Platform references:

- [references/reference-mcp-access.md](references/reference-mcp-access.md)
- [references/reference-rest-access.md](references/reference-rest-access.md)
- [references/reference-polling-and-backoff.md](references/reference-polling-and-backoff.md)
- [references/reference-errors-and-retries.md](references/reference-errors-and-retries.md)
- [references/reference-large-inputs.md](references/reference-large-inputs.md)
- [references/reference-receipts-and-transparency.md](references/reference-receipts-and-transparency.md)
- [references/reference-billing-and-quotes.md](references/reference-billing-and-quotes.md)
- [references/reference-payment-rails.md](references/reference-payment-rails.md)
- [references/reference-policy-selection-and-change-monitoring.md](references/reference-policy-selection-and-change-monitoring.md)
- [references/reference-degraded-and-non-guarantees.md](references/reference-degraded-and-non-guarantees.md)
