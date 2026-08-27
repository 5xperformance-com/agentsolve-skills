# Class Selection

Choose the most specific class whose complete supported boundary fits the real
decision. If a required semantic is deferred, return that deferral before
creating a quote.

| Customer phrasing | Stage 0 decision | Notes |
|---|---|---|
| "shortest tour through these addresses" | `1.1.tsp` | Single directed tour through every node. |
| "one technician visits all stops" | `1.1.tsp` | Use CVRP if capacity or multiple routes matter. |
| "several tours or salespeople" | typed deferral `tsp_multiple_tours` | The nearest TSP subset is one tour. |
| "some locations are optional or have prizes" | typed deferral `tsp_optional_nodes` or `tsp_prize_collecting` | Every TSP node is mandatory. |
| "routes for 5 vans with package weights" | `1.2.vrp.cvrp` | One-depot capacitated routing. |
| "delivery routes with hard arrival windows and service times" | `1.2.vrp.cvrp` | Only the frozen static-travel hard-window subset applies. |
| "pickup from suppliers then deliver to customers" | `1.2.vrp.cvrp` input v4 | Declare `pickup_delivery_pairs`; both stops ride one vehicle, pickup first, and the paired customers declare `demand: 0`. |
| "same customer can be served by several trucks" | typed deferral `split_delivery_vrp` | Each customer is served once. |
| "several depots feed the routes" | `1.2.vrp.cvrp` input v4 | Declare `depots` beside the primary `depot`, and give a vehicle its own `start_depot_id` and `end_depot_id`. |
| "being late costs money rather than being forbidden" | `1.2.vrp.cvrp` input v4 | Declare `soft_time_windows` with `lateness_penalty_per_unit`; a node takes a hard window or a soft one, never both. |
| "each driver has their own shift length" | `1.2.vrp.cvrp` input v4 | Declare a per-vehicle `duration_limit`; where a fleet limit also applies, the tighter binds. |
| "each truck costs money to send out" | `1.2.vrp.cvrp` | Declare per-vehicle `fixed_cost` in distance units; unused vehicles are free. |
| "only certain trucks may serve this site" | `1.2.vrp.cvrp` | Declare `eligible_vehicles` on the restricted customer. |
| "vehicle types or driver skills" | typed deferral `heterogeneous_fleet_vrp` | Declare `fixed_cost` and `eligible_vehicles` instead when those capture the need. |
| "travel time changes during the day" | typed deferral `time_dependent_travel` | Travel data is static. |
| "minimize shipping cost with continuous flows" | `2.1.lp` | All variables and expressions must be linear and continuous. |
| "choose which warehouse opens" | `2.2.milp` | Binary open decisions make it MILP. |
| "our feasibility tolerance is looser than the default" | `2.2.milp` input v2 | Declare `metadata.feasibility_tolerance`; v2 hashes it and the verifier judges at the value you declared. |
| "optimize profit and emissions and return a Pareto frontier" | typed deferral `native_multi_objective_optimization` | A caller-approved scalar objective is a different decision. |
| "quadratic risk minimization" | typed deferral `quadratic_or_conic_optimization` | Do not silently linearize. |
| "chance constrained capacity planning" | typed deferral `chance_constrained_optimization` | Expected-value modelling is not a chance constraint. |
| "how many units should we stock for one sale period" | `3.1.newsvendor` | Explicit independent discrete SKU scenarios. |
| "inventory policy over the next 12 months" | typed deferral `multi_period_inventory` | One static ordering period only. |
| "SKUs share one purchasing budget" | typed deferral `capacity_coupled_inventory` | SKU decisions are independent. |
| "demand is correlated across products" | typed deferral `correlated_inventory` | Scenarios are per SKU. |
| "schedule activities with crews and precedence" | `4.1.scheduling.rcpsp` | Renewable resources and submitted precedences. |
| "materials or cash have one total budget for the project" | `4.1.scheduling.rcpsp` | Declare `non_renewable_resources` budgets and per-mode consumption. |
| "verify this submitted project schedule" | `4.1.scheduling.rcpsp` with `job_intent=verify_only` | The candidate must cover every activity. |
| "durations are random and we need a robust schedule" | typed deferral `stochastic_durations` | Durations are deterministic integers. |
| "optimize makespan and resource smoothing together" | typed deferral `multi_objective_scheduling` | The class objective is makespan only. |
| "schedule jobs through machines in a fixed operation order" | `4.2.scheduling.jssp` | Fixed machine and order per operation. |
| "minimize total lateness against job due dates" | `4.2.scheduling.jssp` with `objectives.primary=minimize_total_tardiness` | Per-job due dates and optional release days. |
| "any qualified machine can do this operation" | `4.2.scheduling.jssp` input v3 | Declare per-operation `machine_options` with the duration on each machine; the receipt names the machine the schedule chose. |
| "late orders differ in how much they cost us" | `4.2.scheduling.jssp` input v3 with `objectives.primary=minimize_total_tardiness` | Declare a per-job `weight`; the payload is rejected when the weighted objective could leave exact integer range. |
| "changeover time depends on what ran before" | typed deferral `jssp_sequence_dependent_setup` | Sequence-dependent setup is not modelled. |
| "roster staff to shifts meeting coverage and fairness" | `4.3.scheduling.rostering` | Dated slots, skill coverage, hard limits, and integer penalties. |
| "a senior can also cover a junior's shift" | `4.3.scheduling.rostering` | Declare `skill_substitution` `[from, to]` pairs; each member's effective skills expand by one hop. |
| "one worker can cover several required roles in the same shift" | typed deferral `rostering_explicit_skill_assignment` | Assignments do not carry an explicit role, including when substitution makes one member cover two required skills in a slot. |
| "staff prefer some shifts to others" | `4.3.scheduling.rostering` input v3 | Declare `assignment_costs` per staff and slot; they price the roster rather than forbidding anything. |
| "employees bid for the shifts they want" | typed deferral `rostering_preference_bidding` | Bidding is not modelled. Declare `assignment_costs` when graded preference is what the bid really expresses. |
| "these people are already promised these shifts" | `4.3.scheduling.rostering` input v3 | Declare `pinned_assignments` and `forbidden_assignments`; both are hard and are validated as eligible and available. |
| "rebuild the roster but change as little as possible" | `4.3.scheduling.rostering` input v3 | Declare `baseline_roster` and a `penalties.churn` weight; the penalty prices every difference from the baseline. |
| "everyone has contracted minimum hours" | `4.3.scheduling.rostering` input v3 | Declare `min_hours` per staff member beside the existing `max_hours`. |
| "assign these unit tasks to people or machines" | `5.1.assignment` | Sparse allowed pairs and integer weights. |
| "each task consumes a different amount of worker time" | typed deferral `assignment_gap_consumption` | v1 consumes one capacity unit per task. |
| "one task needs three people" | typed deferral `assignment_multi_unit_demand` | Tasks are indivisible and unit demand. |
| "match residents to hospitals by preference lists" | typed deferral `assignment_stable_matching` | Weight optimization does not prove stability. |
| "seat guests so compatible pairs sit together" | typed deferral `assignment_quadratic_interaction` | Pairwise interactions are quadratic. |
| "choose the most valuable subset that fits one capacity" | `9.1.knapsack` | Exact integer bounded knapsack; each item defaults to a single copy. |
| "take up to N copies of an item" | `9.1.knapsack` | Set the item's `quantity` bound to the number of copies available. |
| "each item consumes several capacity dimensions" | typed deferral `knapsack_multi_capacity` | One scalar capacity only. |
| "allocate items among several containers" | typed deferral `knapsack_multiple_containers` | One container only. |
| "pack indivisible items into the fewest bins" | `9.3.bin_packing` | Declare `bin_types`; a single unit-cost type gives minimum-count packing, `conflicts` keeps item pairs apart. |
| "keep incompatible items in separate bins" | `9.3.bin_packing` | Set `conflicts` to the item pairs that may not share a bin. |
| "items have several sizes or capacities" | typed deferral `bin_packing_multidimensional` | One size dimension only. |
| "bins have different capacities or costs" | `9.3.bin_packing` | Declare each `{capacity, cost}` in `bin_types`; a used bin is priced at the cheapest type that holds it. |
| "choose the cheapest sets covering every element" | `9.2.set_cover` | Weighted set multicover; set `demand` per element (default 1). |
| "each element needs several independent covers" | `9.2.set_cover` | Set the element's `demand` to the required cover count. |
| "we can leave an element uncovered for a penalty" | `9.2.set_cover` | Set the element's `uncovered_penalty` to the per-unit cost of leaving it short. |
| "send this OR-Tools or HiGHS native payload" | typed deferral `provider_native_payload_required` | Submit the canonical AgentSolve schema. |

Read the selected class reference and the live discovered schema before
constructing the payload.
