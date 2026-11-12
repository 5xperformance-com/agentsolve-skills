# Verification And Certificates

Contents: Class Coverage · Improvement Rounds · Actionability

This is the cross-class answer to "what evidence supports this result?"

- `established_guarantee` is the platform-verifier conclusion: `unverified`,
  `validity`, `global_optimality`, or `infeasibility`.
- `valid_result` means the platform verifier checked result semantics.
- `solver_proved` is solver-sourced and requires an explicit admitted-solver
  proof signal with the exact terminal status required by that class.
- `independent_certificate` is verifier-sourced and names the mathematical
  proposition independently proved.

A raw proof flag, zero gap, equal bound, approximate equality, or objective
recomputation alone cannot create either proof claim.

Validity and proof are separate. When an exact optimality proof is outside the
verifier's proof envelope, a valid result can still carry
`established_guarantee=validity`.

## Class Coverage

- LP: primal and dual feasibility and the recomputed objective are checked at
  the tolerance you declare; strong duality within that tolerance establishes
  `global_optimality`. An exact rational Farkas certificate establishes
  infeasibility for proposition `lp.infeasibility`. Reduced costs are visible
  to the tenant only.
- MILP: independent feasibility/objective checks; bounds, gaps, and public
  proof flags remain diagnostic.
- QP: primal feasibility, objective recomputation, dual signs, stationarity,
  and complementary slackness at the declared tolerance establish
  `global_optimality` for a convex program as a tolerance envelope, not an
  exact certificate, so no `independent_certificate` is issued for it; an
  exact rational Farkas ray establishes infeasibility for proposition
  `qp.infeasibility`; an `unbounded` engine status is refunded as unverified.
- Minimum-cost flow: arc bounds, flow conservation, and objective
  recomputation in exact integer arithmetic; node potentials that pass an exact
  reduced-cost check establish `global_optimality` with proposition
  `min_cost_flow.optimality`, a flow without potentials establishes `validity`,
  and an exact Hoffman cut establishes infeasibility for proposition
  `min_cost_flow.infeasibility`; an infeasible answer without a cut is
  refunded as unverified.
- TSP: route validity, visit coverage, depot return or finish semantics, and
  objective recomputation; where an engine proves its tour optimal, the
  receipt carries that as the solver-sourced `solver_proved` claim;
  `proved_optimal` stays false because the verifier does not certify TSP
  optimality.
- CVRP: route validity, coverage, capacity, hard-window timing,
  service completion, route-duration checks, and objective recomputation;
  an engine's own optimality proof appears as the solver-sourced
  `solver_proved` claim; `proved_optimal` stays false because the verifier
  does not certify routing optimality.
- RCPSP: precedence, renewable-resource capacity, calendars, activity windows,
  mode legality, makespan recomputation, and `proved_optimal` as a diagnostic.
- Newsvendor: selected quantity and expected cost/profit recomputation over
  explicit demand outcomes, plus an exact rational grid-optimality certificate
  inside the published enumeration work cap; false `OPTIMAL` claims inside the
  cap are refuted.
- JSSP and rostering: exact schedule or roster validity and objective
  recomputation; optimality remains solver-sourced.
- Assignment: exact min-cost-flow dual certificates for accepted optima inside
  the verifier's work cap, and deficiency cuts for accepted infeasibility;
  above the cap a result is certified valid, not optimal.
- Knapsack: exact optimum-value recomputation only inside the published DP
  work cap; ties are accepted by value.
- Set cover: exact coverage and cost, with no independent global-optimality
  certificate.
- Bin packing: exact partition and total bin cost, plus exact bounded
  recomputation or the integer volume-lower-bound proposition when applicable.

## Improvement Rounds

The cohort summary says whether more time can help: per-member objectives,
runtimes and agreement ship on every settled portfolio; each member's
receipt carries its `solver_status`, which says how the run ended. A receipt
whose `established_guarantee` is `global_optimality` is terminal for that
instance. The verifier can establish it exactly for minimum-cost flow,
newsvendor, assignment, knapsack and bin packing, where no further round at
any budget can improve the answer. For LP and QP it is established within
the declared tolerance: two answers inside that tolerance can differ, and a
further round is not worth buying. For TSP,
CVRP, MILP, RCPSP, JSSP, rostering and
set cover it certifies validity only, so `proved_optimal` never reads true
there; the stop signal is the engine's own `solver_proved` claim, which is
the solver's word, not the verifier's. Absent either, buy another round
only when that evidence shows headroom: a fresh quote with a larger
`constraints.time_budget_ms`, ten minutes (600000) at most, narrowed to the
contenders, sized from the winner's observed runtime rather than guessed.
When all settled members agree at the best objective and the winner
finished inside its budget, a larger budget is unlikely to change the
answer — that is reasoning, not proof, so the honest report stays
best-found. Resubmitting an unchanged document through the tools replays
the recorded result at no extra cost, because the tools reuse the
idempotency key; the same input under a new key is a new paid job. A
deliberate paid re-roll can change the answer only where an engine is
stochastic. Stop after one round without improvement. Improvement comes
from platform rounds, never local heuristics.

## Actionability

Tenant-scoped results can include richer result payloads and reduced costs.
Public transparency receipts may redact commercial split amounts and tenant-only
details. Act on verifier-recomputed validity and settled job output first; use
named receipt claims to determine proof source and proposition, and diagnostics
only to explain quality, warnings, and limitations.
