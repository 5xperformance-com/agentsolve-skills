# Method: Combinatorial Routing

Stage 0 routing covers TSP, CVRP, and the hard-window CVRP subset. Start at
[problem-type-tsp.md](problem-type-tsp.md) for one-tour routing and
[problem-type-vrp-cvrp.md](problem-type-vrp-cvrp.md) for fleets,
capacity, and hard windows.

## Family Scope

- `1.1.tsp`: one tour over all required nodes.
- `1.2.vrp.cvrp`: one depot, several vehicles, hard capacities, directed
  distances, and optional hard-window timing fields.
- VRPTW-lite: the CVRP launch subset with hard windows, service times, travel
  times, and route-duration checks.

## Verifier Contract

The verifier recomputes route validity, node coverage, objective value,
capacity for CVRP, hard-window timing propagation, service completion,
route-duration limits, and depot return or finish semantics. Use
`routing_infeasibility_certificate` for routing-specific infeasibility.

## Practical Methods

Exact TSP and small routing cases may use branch-and-cut style reasoning.
Classic DFJ and MTZ formulations are useful modelling intuition, not payload
dialects. Christofides-style guarantees apply only to metric symmetric TSP and
must not be generalized to arbitrary directed matrices. LKH-style heuristics,
HGS/PyVRP-style heuristics, insertion construction, push-forward hard-window
checks, and OR-Tools Routing may appear as backend method awareness, but the
caller still sends canonical AgentSolve schemas only.

## Deferral Cross-Reference

Use typed deferral guidance for `pickup_delivery_vrp`, `split_delivery_vrp`,
`multi_depot_vrp`, `heterogeneous_fleet_vrp`, `soft_time_windows_vrp`, and
`time_dependent_travel`. Full driver-rule routing is nearest to the CVRP
hard-window subset only when the unsupported semantics are removed by the
caller.

For evidence interpretation, see
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
