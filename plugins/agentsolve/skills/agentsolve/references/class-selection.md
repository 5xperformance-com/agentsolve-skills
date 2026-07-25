# Class Selection

This one-hop reference mirrors the common phrasing map from
`docs/contracts/stage-0-class-selection-and-modelling-boundary.md` section 2.
That contract remains the source of truth; update this projection only from the
boundary map.

| Customer phrasing | Stage 0 decision | Notes |
|---|---|---|
| "shortest tour through these addresses" | `1.1.tsp` | Single-tour routing. |
| "one technician visits all stops" | `1.1.tsp` | Use CVRP only if vehicle capacity or multiple routes matter. |
| "routes for 5 vans with package weights" | `1.2.vrp.cvrp` | Pure CVRP fits Stage 0. |
| "delivery routes with hard arrival windows and service times" | `1.2.vrp.cvrp` within the launch VRPTW-lite subset | Hard windows are accepted only inside the current v2 schema/verifier subset. |
| "VRPTW plus regulatory driver breaks" | typed deferral `time_dependent_travel` | Nearest subset is CVRP/VRPTW-lite; regulatory break logic is not in Stage 0. |
| "pickup from suppliers then deliver to customers" | typed deferral `pickup_delivery_vrp` | Do not remodel as ordinary CVRP unless pickup/delivery pairing is not required. |
| "same customer can be served by several trucks" | typed deferral `split_delivery_vrp` | Split delivery is outside the launch verifier. |
| "several depots feed the routes" | typed deferral `multi_depot_vrp` | One depot only at Stage 0. |
| "different vehicle types with fixed costs and skills" | typed deferral `heterogeneous_fleet_vrp` | Per-vehicle capacity is not full heterogeneous fleet support. |
| "minimize shipping cost with continuous flows" | `2.1.lp` | Use LP if all constraints and costs are linear. |
| "choose which warehouse opens" | `2.2.milp` | Binary facility-open decisions make it MILP. |
| "optimize profit and emissions and return a Pareto frontier" | typed deferral `native_multi_objective_optimization` | A single weighted objective may be modelled if the caller accepts fixed weights and no frontier. |
| "quadratic risk minimization" | typed deferral `quadratic_or_conic_optimization` | Do not linearize unless the caller explicitly accepts a linear approximation as the actual model. |
| "chance constrained capacity planning" | typed deferral `chance_constrained_optimization` | Expected-value LP/MILP is allowed only if chance constraints are not required. |
| "how many units should we stock for one sale period" | `3.1.newsvendor` | Explicit discrete scenarios and expected cost/profit fit. |
| "inventory policy over the next 12 months" | typed deferral `multi_period_inventory` | Multi-period inventory is Stage 1+ roadmap work. |
| "schedule activities with crews and precedence" | `4.1.scheduling.rcpsp` | Renewable resources and precedence scheduling fit. |
| "verify this submitted project schedule" | `4.1.scheduling.rcpsp` with `job_intent=verify_only` | Candidate schedule support is launch-facing in the current boundary. |
| "durations are random and we need a robust schedule" | typed deferral `stochastic_durations` | Deterministic durations only. |
| "optimize makespan and resource smoothing together" | typed deferral `multi_objective_scheduling` | A single linear penalty model may be MILP only if the caller accepts it as one objective. |
| "send this OR-Tools or HiGHS native payload" | typed deferral `provider_native_payload_required` | Stage 0 accepts canonical AgentSolve schemas only. |

`JSSP` is planned only. Route arbitrary job-shop scheduling requests to the
boundary contract before drafting any payload.
