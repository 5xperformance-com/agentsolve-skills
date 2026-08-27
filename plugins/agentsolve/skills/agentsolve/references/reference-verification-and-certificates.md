# Verification And Certificates

This is the cross-class answer to "what evidence supports this result?"

- `established_guarantee` is the platform-verifier conclusion: `unverified`,
  `validity`, `global_optimality`, or `infeasibility`.
- `valid_result` means the platform verifier checked result semantics.
- `solver_proved` is solver-sourced and requires an explicit admitted-adapter
  proof signal with the exact terminal status required by that class.
- `independent_certificate` is verifier-sourced and names the mathematical
  proposition independently proved.

A raw proof flag, zero gap, equal bound, approximate equality, or objective
recomputation alone cannot create either proof claim.

Validity and proof are separate. When an exact optimality proof is outside the
verifier's proof envelope, a valid result can still carry
`established_guarantee=validity`.

## Class Coverage

- LP: primal feasibility, objective recomputation, dual values where populated,
  complementary-slackness intuition, infeasible/unbounded interpretation, and
  reduced-cost visibility limits.
- MILP: independent feasibility/objective checks; bounds, gaps, and public
  proof flags remain diagnostic.
- TSP: route validity, visit coverage, depot return or finish semantics, and
  objective recomputation.
- CVRP/VRPTW-lite: route validity, coverage, capacity, hard-window timing,
  service completion, route-duration checks, and objective recomputation.
- RCPSP: precedence, renewable-resource capacity, calendars, activity windows,
  mode legality, makespan recomputation, and `proved_optimal` as a diagnostic.
- Newsvendor: selected quantity and expected cost/profit recomputation over
  explicit demand outcomes, plus an exact rational grid-optimality certificate
  inside the published enumeration work cap; false `OPTIMAL` claims inside the
  cap are refuted.
- JSSP and rostering: exact schedule or roster validity and objective
  recomputation; optimality remains solver-sourced.
- Assignment: exact min-cost-flow dual certificates for accepted optima and
  deficiency cuts for accepted infeasibility.
- Knapsack: exact optimum-value recomputation only inside the published DP
  work cap; ties are accepted by value.
- Set cover: exact coverage and cost, with no independent global-optimality
  certificate.
- Bin packing: exact partition and count, plus exact bounded recomputation or
  the integer volume-lower-bound proposition when applicable.

## Actionability

Tenant-scoped results can include richer result payloads and reduced costs.
Public transparency receipts may redact commercial split amounts and tenant-only
details. Act on verifier-recomputed validity and settled job output first; use
named receipt claims to determine proof source and proposition, and diagnostics
only to explain quality, warnings, and limitations.
