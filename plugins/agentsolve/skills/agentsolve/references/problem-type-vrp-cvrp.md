# Problem Type: CVRP, Fleet Sizing, And VRPTW-Lite

Canonical schema versions:

- Input: `1.2.vrp.cvrp.input.v4`
- Output: `1.2.vrp.cvrp.output.v4`

Use `1.2.vrp.cvrp` for one-depot, multiple-vehicle routing with hard
capacities, customer demand, directed travel costs, optional per-vehicle fixed
costs (fleet sizing), optional per-customer vehicle eligibility, and the
launch hard-window subset when service times and travel times are supplied.

For submission, use [reference-rest-access.md](reference-rest-access.md)
or [reference-mcp-access.md](reference-mcp-access.md).

Solver availability is discovered through menu, quote, and receipt fields.
Additional routing families may improve quality or latency after admission, but
agents should keep emitting the canonical CVRP/VRPTW-lite schema rather than any
backend-specific model.

## Formulation Recipe

- Required: `depot`, `vehicle_count`, `vehicle_capacity`, `customers[].demand`,
  and complete directed `distances`.
- Optional launch fields: `vehicles[].capacity`, `vehicles[].fixed_cost`, a
  default `vehicle_fixed_cost`, `customers[].eligible_vehicles`, hard
  `time_windows`, `service_times`, complete directed `travel_times`, and
  `route_duration_limit`.
- Objective: minimize one scalar total cost — the sum of traversed `distances`
  entries plus the `fixed_cost` of every vehicle that serves at least one
  customer. With no fixed costs this is the classic total-distance objective.
- Units: `fixed_cost` values share the unit of the `distances` matrix; keep
  distance and travel-time units internally consistent; service times and
  windows use the same time base.
- Eligibility: `eligible_vehicles` is a hard constraint — only the listed
  vehicles may serve that customer. Omit it for customers any vehicle may
  serve.
- Complexity tier: CVRP customer-count tiers are `S <= 25`, `M <= 75`, and
  `L > 75`, excluding the depot. The open-ended L band is not a capacity or
  latency guarantee. Inspect vehicle count, matrix and eligibility density,
  time constraints, pickup-delivery pairs, and depots in the quote descriptor.

## Deferrals And Routing Choices

| Required semantic | Action |
|---|---|
| split delivery | code `split_delivery_vrp`, nearest_supported_subset `1.2.vrp.cvrp`, roadmap_status `deferred` |
| vehicle skills or full fleet types | code `heterogeneous_fleet_vrp`, nearest_supported_subset per-vehicle capacity, fixed cost, and explicit eligibility, roadmap_status `deferred` |
| time-varying travel | code `time_dependent_travel`, nearest_supported_subset static matrix routing, roadmap_status `deferred` |

Paired pickup and delivery, several depots, and soft windows are supported
schema fields:

- `pickup_delivery_pairs` names a `pickup_id`, a `delivery_id`, and the
  `quantity` that rides between them. Both customers declare `demand: 0` — the
  pair's quantity is the flow. One vehicle carries the pair, pickup first, and
  capacity bounds what is on board at every stop rather than the route total.
- `depots` names additional depots beside the required `depot`, and a vehicle
  may declare `start_depot_id`, `end_depot_id`, and its own `duration_limit`.
  Omit them and the vehicle works the primary depot under the fleet limit.
- `soft_time_windows` prices lateness instead of forbidding it: a node declares
  `start`, `end`, and `lateness_penalty_per_unit`, and any service starting
  after `end` adds that price per unit to the objective. A node declares either
  a hard window or a soft one, never both.

Per-vehicle fixed costs and explicit eligibility are supported schema fields,
not deferrals: model a skill requirement as an explicit `eligible_vehicles`
list when the qualifying vehicles are known.

## Output And Self-Checks

The output cites `1.2.vrp.cvrp.output.v4`. Read `routes[].vehicle_id`,
`routes[].stops[]`, load or cumulative-load values, distance, duration,
top-level `total_distance`, `total_fixed_cost`, and `total_cost`, and
conditional timing fields `arrival_time`, `service_start_time`, and
`service_completion_time` when hard windows are present. A vehicle omitted
from `routes[]` was not deployed and incurs no fixed cost.

Before quote creation, check that total demand does not exceed aggregate
capacity, every customer's demand fits at least one of its eligible vehicles,
every customer appears once, the depot is present, all matrix arcs exist, and
hard windows can be reached under the supplied travel-time matrix.
`routing_infeasibility_certificate` is the routing diagnostic label for
capacity, coverage, timing, or duration impossibility; semantic pre-check
failures are request corrections before retry.

## Minimal REST Sketch

```json
{
  "idempotency_key": "quote-cvrp-001",
  "problem_type": "1.2.vrp.cvrp",
  "problem_schema_version": "1.2.vrp.cvrp.input.v4",
  "input": {
    "depot": "depot",
    "vehicle_count": 2,
    "vehicle_capacity": 10,
    "vehicle_fixed_cost": 25,
    "customers": [
      {"id": "c1", "demand": 4},
      {"id": "c2", "demand": 6, "eligible_vehicles": ["veh_2"]}
    ],
    "distances": {
      "depot": {"depot": 0, "c1": 7, "c2": 9},
      "c1": {"depot": 7, "c1": 0, "c2": 3},
      "c2": {"depot": 9, "c1": 3, "c2": 0}
    }
  }
}
```

## Minimal MCP Sketch

```json
{
  "name": "agentsolve.quotes.create",
  "arguments": {
    "idempotency_key": "quote-cvrp-001",
    "problem_type": "1.2.vrp.cvrp",
    "problem_schema_version": "1.2.vrp.cvrp.input.v4"
  }
}
```

Common pitfalls: capacity-overflow routes, missing depot arcs, inconsistent
time units, impossible hard windows, decimal costs without scaling, fixed
costs stated in money units while distances use another unit, an
`eligible_vehicles` list naming undeclared vehicles, and mistaking per-vehicle
capacity for full fleet-type modelling.

For formulation and result-confidence guidance, see
[formulation-patterns.md](formulation-patterns.md),
[infeasibility-diagnostics.md](infeasibility-diagnostics.md), and
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
