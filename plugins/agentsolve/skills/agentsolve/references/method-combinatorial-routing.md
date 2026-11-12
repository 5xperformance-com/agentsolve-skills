# Method: Combinatorial Routing

Routing covers TSP and CVRP: fleet sizing, eligibility, several depots, paired
pickup and delivery, and hard or priced-soft time windows. Start at
[problem-type-tsp.md](problem-type-tsp.md) for one-tour routing and
[problem-type-vrp-cvrp.md](problem-type-vrp-cvrp.md) for fleets,
capacity, fixed costs, eligibility, depots, and time windows.

## Family Scope

- `1.1.tsp`: one tour over all required nodes.
- `1.2.vrp.cvrp`: one or more depots, several vehicles, hard capacities,
  directed distances, optional per-vehicle fixed costs and per-customer vehicle
  eligibility, optional paired pickup and delivery, and optional time windows
  with service times, travel times, and route-duration checks.

## Verifier Contract

The verifier recomputes route validity, node coverage, the objective value
(for CVRP: distance plus used-vehicle fixed cost plus any lateness penalty),
capacity and eligibility for CVRP, hard-window timing propagation, service
completion, route-duration limits, and depot return or finish semantics. When
it rejects a result, the diagnostic label is `semantic_diagnostic`.

## Practical Methods

Classic DFJ and MTZ formulations are useful modelling intuition, not payload
dialects. Christofides-style guarantees apply only to metric symmetric TSP and
must not be generalized to arbitrary directed matrices. LKH-style heuristics,
HGS/PyVRP-style heuristics, insertion construction, push-forward hard-window
checks, and OR-Tools Routing may appear as backend method awareness, but the
caller still sends canonical AgentSolve schemas only.

## Deferral Cross-Reference

On CVRP input v4, use typed deferral guidance for `split_delivery_vrp`,
`heterogeneous_fleet_vrp`, and `time_dependent_travel`. Paired pickup and
delivery, multiple depots, and priced lateness are carried by v4 itself.
Input v3 is the one earlier version that still runs, and it defers them, so
the version a payload declares decides which guidance applies. Full
driver-rule routing fits CVRP only when the remaining unsupported semantics
are removed by the caller.

For evidence interpretation, see
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
