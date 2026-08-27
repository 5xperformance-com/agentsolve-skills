# Method: Combinatorial Routing

Stage 0 routing covers TSP, CVRP with fleet sizing and eligibility, and the
hard-window CVRP subset. Start at
[problem-type-tsp.md](problem-type-tsp.md) for one-tour routing and
[problem-type-vrp-cvrp.md](problem-type-vrp-cvrp.md) for fleets,
capacity, fixed costs, eligibility, and hard windows.

## Family Scope

- `1.1.tsp`: one tour over all required nodes.
- `1.2.vrp.cvrp`: one depot, several vehicles, hard capacities, directed
  distances, optional per-vehicle fixed costs and per-customer vehicle
  eligibility, and optional hard-window timing fields.
- VRPTW-lite: the CVRP launch subset with hard windows, service times, travel
  times, and route-duration checks.

## Verifier Contract

The verifier recomputes route validity, node coverage, the objective value
(distance plus used-vehicle fixed cost for CVRP), capacity and eligibility for
CVRP, hard-window timing propagation, service completion, route-duration
limits, and depot return or finish semantics. Use
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

On CVRP input v4, use typed deferral guidance for `split_delivery_vrp`,
`heterogeneous_fleet_vrp`, and `time_dependent_travel`. Paired pickup and
delivery, multiple depots, and priced lateness are carried by v4 itself;
earlier readable versions still defer them, so the version a payload declares
decides which guidance applies. Full driver-rule routing is nearest to the CVRP
subset only when the remaining unsupported semantics are removed by the caller.

For evidence interpretation, see
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
