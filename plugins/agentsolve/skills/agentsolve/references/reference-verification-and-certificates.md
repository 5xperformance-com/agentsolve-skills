# Verification And Certificates

This is the cross-class answer to "what evidence supports this result?" It
distinguishes verifier-recomputed facts, backend proof diagnostics, heuristic
quality signals, and receipt visibility boundaries.

## Class Coverage

- LP: primal feasibility, objective recomputation, dual values where populated,
  complementary-slackness intuition, infeasible/unbounded interpretation, and
  reduced-cost visibility limits.
- MILP: best incumbent, `best_bound`, `optimality_gap`,
  `optimality_certified`, and time-limit semantics.
- TSP: route validity, visit coverage, depot return or finish semantics, and
  objective recomputation.
- CVRP/VRPTW-lite: route validity, coverage, capacity, hard-window timing,
  service completion, route-duration checks, and objective recomputation.
- RCPSP: precedence, renewable-resource capacity, calendars, activity windows,
  mode legality, makespan recomputation, and `proved_optimal` as a diagnostic.
- Newsvendor: selected quantity and expected cost/profit recomputation over
  explicit demand outcomes.

## Actionability

Tenant-scoped results can include richer result payloads and reduced costs.
Public transparency receipts may redact commercial split amounts and tenant-only
details. Act on verifier-recomputed validity and settled job output first; use
receipt diagnostics to explain quality, warnings, and limitations. Raw backend
proof artifacts and exact rational certificates are not Stage 0 public outputs.
