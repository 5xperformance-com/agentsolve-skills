# Problem Type: CVRP And VRPTW-Lite

Canonical schema versions:

- Input: `1.2.vrp.cvrp.input.v2`
- Output: `1.2.vrp.cvrp.output.v2`

Use `1.2.vrp.cvrp` for one-depot, multiple-vehicle routing with hard
capacities, customer demand, directed travel costs, and the launch hard-window
subset when service times and travel times are supplied.

For submission, use [reference-rest-access.md](reference-rest-access.md)
or [reference-mcp-access.md](reference-mcp-access.md).

Solver availability is discovered through menu, quote, and receipt fields.
Additional routing families may improve quality or latency after admission, but
agents should keep emitting the canonical CVRP/VRPTW-lite schema rather than any
backend-specific model.

## Formulation Recipe

- Required: `depot`, `vehicle_count`, `vehicle_capacity`, `customers[].demand`,
  and complete directed `distances`.
- Optional launch fields: `vehicles[].capacity`, hard `time_windows`,
  `service_times`, complete directed `travel_times`, and `route_duration_limit`.
- Objective direction: minimize total distance, travel time, or canonical cost
  as selected by the schema.
- Units: keep distance and travel-time units internally consistent; service
  times and windows use the same time base.
- Complexity tier: CVRP customer-count tiers are `S <= 25`, `M <= 75`, and
  `L > 75`, excluding the depot.

## Deferrals And Routing Choices

| Required semantic | Action |
|---|---|
| pickup/delivery pairing | code `pickup_delivery_vrp`, nearest_supported_subset `1.2.vrp.cvrp`, roadmap_status `deferred` |
| split delivery | code `split_delivery_vrp`, nearest_supported_subset `1.2.vrp.cvrp`, roadmap_status `deferred` |
| several depots | code `multi_depot_vrp`, nearest_supported_subset `1.2.vrp.cvrp`, roadmap_status `deferred` |
| fixed costs, skills, or full fleet types | code `heterogeneous_fleet_vrp`, nearest_supported_subset `1.2.vrp.cvrp`, roadmap_status `deferred` |
| soft windows | code `soft_time_windows_vrp`, nearest_supported_subset hard windows, roadmap_status `deferred` |
| time-varying travel | code `time_dependent_travel`, nearest_supported_subset static matrix routing, roadmap_status `deferred` |

## Output And Self-Checks

The output cites `1.2.vrp.cvrp.output.v2`. Read `routes[].vehicle_id`,
`routes[].stops[]`, load or cumulative-load values, distance, duration, and
conditional timing fields `arrival_time`, `service_start_time`, and
`service_completion_time` when hard windows are present.

Before quote creation, check that total demand does not exceed aggregate
capacity, every customer appears once, the depot is present, all matrix arcs
exist, and hard windows can be reached under the supplied travel-time matrix.
`routing_infeasibility_certificate` is the routing diagnostic label for
capacity, coverage, timing, or duration impossibility; semantic pre-check
failures are request corrections before retry.

## Minimal REST Sketch

```json
{
  "idempotency_key": "quote-cvrp-001",
  "problem_type": "1.2.vrp.cvrp",
  "problem_schema_version": "1.2.vrp.cvrp.input.v2",
  "input": {
    "depot": "depot",
    "vehicle_count": 2,
    "vehicle_capacity": 10,
    "customers": [{"id": "c1", "demand": 4}, {"id": "c2", "demand": 6}],
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
    "problem_schema_version": "1.2.vrp.cvrp.input.v2"
  }
}
```

Common pitfalls: capacity-overflow routes, missing depot arcs, inconsistent
time units, impossible hard windows, decimal costs without scaling, and
mistaking per-vehicle capacity for full fleet-type modelling.

For formulation and result-confidence guidance, see
[formulation-patterns.md](formulation-patterns.md),
[infeasibility-diagnostics.md](infeasibility-diagnostics.md), and
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
