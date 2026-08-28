---
name: agentsolve
description: Use when selecting an AgentSolve problem class or driving the canonical quote -> job -> poll flow without solver-native or engine-internal payloads.
---

# AgentSolve

Use this skill to classify a request, choose the canonical problem type, draft
against the active canonical schema, create a quote, create a job, and poll the
job to a terminal state.

## Getting Started

Happy path for a first integration:

1. Read [references/class-selection.md](references/class-selection.md) and
   choose one of the twelve launch-scoped optimization classes below.
2. Create `POST /v1/quotes` with canonical input, a stable idempotency key, and
   the required `policy` — `max_price_usdc` at minimum
   ([references/reference-policy-selection-and-change-monitoring.md](references/reference-policy-selection-and-change-monitoring.md)).
3. Read the quote response's `candidates` and `payment_requirement`.
4. Choose an explicit routing mode for `POST /v1/jobs`:
   - agent-chosen solver: pass `selected_algorithms: ["<solver_admission_id>"]`
   - portfolio comparison: pass `selected_algorithms` with 2 to 10 ids
   - platform default: pass `auto_route: true` for the deterministic
     catalog-default selection (ranked by trust, then quality, then latency,
     then price)
   When the task asks for the best achievable solution, portfolio mode is
   the fit: submit all eligible candidates from the quote (up to 10) and
   compare their verifier-accepted results, accepting that the job price
   multiplies by the cohort size. One engine is one data point; a
   find-the-best answer needs the field, and cohort agreement is an
   algorithmic cross-check — every member's result is separately
   verifier-checked, and the members are distinct algorithms running on
   one platform (the receipt's `degraded_mode` and
   `independent_family_count_bucket` state exactly what "independent"
   means for a given job — reconcile claims with those fields).
   Portfolio jobs pay from account
   credit or trial credit — the Stripe rail rejects portfolios by design.
   If the quote bound solver hints (anything you sent under `constraints`),
   pass the quote's `effective_solver_hints` back verbatim as the job's
   `solver_hints`; a mismatch is rejected. Units differ by layer:
   `constraints.time_budget_ms` is milliseconds at the quote, and the
   hint it folds into (`time_limit_seconds`) is seconds on the job —
   the quote does that conversion; never hand-build the hint.
5. Satisfy exactly one available payment option from `payment_requirement`.
   Omit `payment` only when `payment_requirement.requires_payment=false`.
6. Poll `GET /v1/jobs/{job_id}` until `SETTLED`, `REFUNDED`, `DISPUTED`, or
   `SUPERSEDED`, then read output and receipt together.

## Native instance files

If the problem arrives as standard benchmark or industry files, translate
them deterministically instead of hand-writing canonical JSON: run
`python tools/translate.py FILE1 FILE2 ...` (TSPLIB `.tsp`/`.atsp`, CVRPLIB
`.vrp`, MPS `.mps`/`.mps.gz`, PSPLIB single-mode `.sm`, and Taillard files;
canonical documents land in the working directory or `--out-dir`, never
beside the inputs), review the written `*.canonical.json`, then run
`python tools/submit.py A.canonical.json B.canonical.json C.canonical.json
--out-dir DIR` to quote, fund, submit, poll, and write results named after
each source instance — including `.tour`/`.sol` files for TSP and CVRP —
into the directory your task expects. Submit every document in ONE
invocation: the tool batches with bounded concurrency and absorbs
rate-limit backoff itself; launching parallel submit processes is what
trips the queue limits. (Both tools run on the standard library alone; in a
network-restricted sandbox, allow access to the AgentSolve base URL.)
Add `--portfolio` for find-the-best tasks (all eligible candidates, up to 10,
at cohort-size times the price): the tool polls the whole cohort with
labelled N/M progress, obtains each settled member's result separately as
its own attributed artifact (`FILE.<engine>.result.json` with that member's
receipt — a portfolio doubles as a benchmarking sweep and an algorithmic
cross-check), and emits the best by the problem's objective sense as the
headline answer. `--settled-threshold N` is both a ranking device (take the
best of the first N responses) and the stall bound — if a cohort stalls, N
caps the wait. A cohort that delivers fewer settled members than expected
without a threshold fails loudly rather than presenting a remnant's answer.
`--select ID ...` submits an explicit cohort and `--auto-route` the platform
default; `--quote-only` prices an experiment before buying it, and
`--detach`/`--resume` decouple submission from waiting. The tool funds from
an active account-credit authority first and falls back to an enrolled
faucet program automatically when no other rail is fundable. The price
ceiling is `--max-price-usdc` (or `AGENTSOLVE_MAX_PRICE_USDC`, default
1.00) — a portfolio's total is the SUM of member prices and is checked
against the same ceiling, so raise it for large cohorts.
Unrecognized dialects are rejected, never approximated; coverage and rules in
[references/reference-native-formats.md](references/reference-native-formats.md).

Start with [references/class-selection.md](references/class-selection.md) when
the request is ambiguous, especially for routing, scheduling, inventory,
integer allocation, or any wording that sounds like a deferred variant.

## Verification is included

Every settled result arrives verifier-attested: the platform verifier
independently recomputes the objective and checks result validity before
settlement, and a portfolio's members are algorithmically independent
engines — distinct algorithms on one platform — cross-checking one
another's answers. Before repeating an independence claim, reconcile it
with the receipt's `degraded_mode` and `independent_family_count_bucket`
fields: they state exactly what "independent" means for that job. You do
not need to build or run your own solver to gain confidence in a platform
result — if the task ships its own checker, run it on the returned
solution files, and read the receipt's
`established_guarantee` for what was and was not proved
([references/reference-verification-and-certificates.md](references/reference-verification-and-certificates.md)).
Absent an optimality certificate, report the best verified objective as
best-found, not proven optimal. The cohort summary tells you whether more
time can help: per-member objectives, runtimes, and agreement ship on
every settled portfolio, and the platform flags when the winning engine
finished well inside its budget. Buy another round only when that
evidence shows headroom — a fresh quote with a larger
`constraints.time_budget_ms` (`submit.py --time-budget-ms`),
`--select`-narrowed to the contenders, sized from the winner's observed
runtime rather than guessed. Resubmitting an unchanged document replays
the recorded result at no extra cost; a deliberate paid re-roll
(`--rerun`) can change the answer only where an engine is stochastic.
Stop after one round without improvement; `--settled-threshold N` is the
stall bound. Improvement comes from platform rounds, never local
heuristics.

Funding is quote-bound. When funding a job, list your payment authorities
first (`GET /v1/payments/authorities`) and prefer an active account-credit
authority; trial credit and a Stripe preflight are the fallbacks. Implemented
paths are account credit with an explicit `PaymentAuthority`,
x402 exact-USDC payment, Stripe PaymentIntent preflight plus Stripe-side
confirmation, and trial-credit redemption. Follow the
quote-level `available` flag for every rail; see
[references/reference-billing-and-quotes.md](references/reference-billing-and-quotes.md)
and [references/reference-payment-rails.md](references/reference-payment-rails.md).
`stripe_spt` remains review-gated and must not be used unless a quote marks it
`available=true`. Rail availability is a quote fact, x402 included: the
quote's payment options say what is available right now — use what the
quote offers.

Launch-scoped classes:

- `1.1.tsp`
- `1.2.vrp.cvrp`
- `2.1.lp`
- `2.2.milp`
- `3.1.newsvendor`
- `4.1.scheduling.rcpsp`
- `4.2.scheduling.jssp`
- `4.3.scheduling.rostering`
- `5.1.assignment`
- `9.1.knapsack`
- `9.2.set_cover`
- `9.3.bin_packing`

Canonical flow:

1. Classify the request from the customer phrasing and boundary map.
2. Confirm the active problem type and schema versions from discovery.
3. Draft the provider-neutral canonical input only.
4. Create the quote, keeping the same problem type and input schema version.
5. Create the job from the accepted quote.
6. Poll until terminal, then read the output and receipt together.

Non-guarantees to preserve in agent-facing answers:

- No global optimality claim unless the returned evidence certifies it.
- No claim that AgentSolve covers every optimization or inference domain.
- No provider-hosted privacy guarantee or enclave-backed execution claim.
- No decentralization or governance-by-stake claim.
- No zero-variance latency or price forecast claim.

Guardrails:

- Use canonical AgentSolve schemas only.
- Do not infer support for deferred variants from nearby launch classes.
- Do not expose internal engine surfaces, internal error shapes, or solver
  implementation payloads.
- Keep formulation detail in one-hop `references/*` files as they are authored.

Problem-type references (per class: schema versions, formulation recipe,
sizing bands, and the class boundary — read only the class you selected):

- [references/problem-type-tsp.md](references/problem-type-tsp.md)
- [references/problem-type-vrp-cvrp.md](references/problem-type-vrp-cvrp.md)
- [references/problem-type-newsvendor.md](references/problem-type-newsvendor.md)
- [references/problem-type-lp.md](references/problem-type-lp.md)
- [references/problem-type-milp.md](references/problem-type-milp.md)
- [references/problem-type-rcpsp.md](references/problem-type-rcpsp.md)
- [references/problem-type-jssp.md](references/problem-type-jssp.md)
- [references/problem-type-rostering.md](references/problem-type-rostering.md)
- [references/problem-type-assignment.md](references/problem-type-assignment.md)
- [references/problem-type-knapsack.md](references/problem-type-knapsack.md)
- [references/problem-type-set-cover.md](references/problem-type-set-cover.md)
- [references/problem-type-bin-packing.md](references/problem-type-bin-packing.md)

Method references (modelling guidance; read when formulating, not for API
mechanics):

- [references/method-combinatorial-routing.md](references/method-combinatorial-routing.md) — routing formulation practice
- [references/method-linear-programming.md](references/method-linear-programming.md) — LP formulation practice
- [references/method-mixed-integer-linear-programming.md](references/method-mixed-integer-linear-programming.md) — MILP formulation practice
- [references/method-stochastic-newsvendor.md](references/method-stochastic-newsvendor.md) — scenario-demand formulation practice
- [references/method-constraint-programming-scheduling.md](references/method-constraint-programming-scheduling.md) — scheduling formulation practice
- [references/formulation-patterns.md](references/formulation-patterns.md) — cross-class formulation patterns
- [references/infeasibility-diagnostics.md](references/infeasibility-diagnostics.md) — reading infeasibility output
- [references/reference-verification-and-certificates.md](references/reference-verification-and-certificates.md) — what verification does and does not establish

Platform references (API mechanics; read the one matching the step you are
on):

- [references/reference-mcp-access.md](references/reference-mcp-access.md) — MCP lifecycle, tool inventory, scopes
- [references/reference-rest-access.md](references/reference-rest-access.md) — endpoints, auth, quote/job creation rules
- [references/reference-polling-and-backoff.md](references/reference-polling-and-backoff.md) — poll cadence and terminal states
- [references/reference-errors-and-retries.md](references/reference-errors-and-retries.md) — error-code inventory and retry rules
- [references/reference-large-inputs.md](references/reference-large-inputs.md) — the 1 MiB inline cap and input transport posture
- [references/reference-native-formats.md](references/reference-native-formats.md) — client-side translators for common native instance formats
- [references/reference-receipts-and-transparency.md](references/reference-receipts-and-transparency.md) — receipt fields and transparency records
- [references/reference-billing-and-quotes.md](references/reference-billing-and-quotes.md) — quote flow, solver-hint binding, funding paths
- [references/reference-payment-rails.md](references/reference-payment-rails.md) — per-rail details and availability rules
- [references/reference-policy-selection-and-change-monitoring.md](references/reference-policy-selection-and-change-monitoring.md) — policy fields and change monitoring
- [references/reference-degraded-and-non-guarantees.md](references/reference-degraded-and-non-guarantees.md) — degraded modes and claim limits
