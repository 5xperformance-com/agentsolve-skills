# Problem Type: TSP

Canonical schema versions:

- Input: `1.1.tsp.input.v1`
- Output: `1.1.tsp.output.v1`

Use `1.1.tsp` when one vehicle or one agent must visit each required node once
and return to the start or finish a single tour. Common user wording includes
"route through all stops" and "visit every customer once and return".

For platform transport, pair this file with
[reference-rest-access.md](reference-rest-access.md) or
[reference-mcp-access.md](reference-mcp-access.md), plus
[reference-polling-and-backoff.md](reference-polling-and-backoff.md).

## Formulation Recipe

- Inputs: stable node IDs, a complete directed distance or cost matrix, and a
  start/depot node when required by the schema.
- Objective direction: minimize total route distance or cost.
- Units: keep every matrix entry in the same unit; seconds, minutes, meters,
  miles, and currency costs must not be mixed.
- Normalization: include every node exactly once in the input set; use integer
  scaled costs when source data is decimal.
- Complexity tier: use node count and matrix completeness as the first sizing
  check; see `docs/engine/OPTIMIZATION_MODELLING_BRIEF.md`.

## Boundary

If capacity, multiple vehicles, hard arrival windows, pickup/delivery pairing,
split delivery, several depots, soft windows, or time-varying travel is
required, do not force the request into TSP.

Typed deferral guidance:

| Required semantic | Action |
|---|---|
| multiple vehicles or capacity | consider `1.2.vrp.cvrp` when one depot and hard capacities fit |
| hard arrival windows with service times | consider the CVRP launch subset when all fields fit |
| pickup/delivery pairing | code `pickup_delivery_vrp`, nearest_supported_subset `1.2.vrp.cvrp`, roadmap_status `deferred` |
| split delivery | code `split_delivery_vrp`, nearest_supported_subset `1.2.vrp.cvrp`, roadmap_status `deferred` |
| several depots | code `multi_depot_vrp`, nearest_supported_subset `1.2.vrp.cvrp`, roadmap_status `deferred` |
| soft windows | code `soft_time_windows_vrp`, nearest_supported_subset `1.2.vrp.cvrp`, roadmap_status `deferred` |
| time-varying travel | code `time_dependent_travel`, nearest_supported_subset `1.2.vrp.cvrp`, roadmap_status `deferred` |

## Result Interpretation

The output cites `1.1.tsp.output.v1` and should be read as an ordered tour with
objective value. Check route validity, visit-once coverage, return/finish
semantics, and objective recomputation from the input matrix. Receipts may show
quality evidence, but do not claim global optimality unless the result evidence
certifies it.

Use a haversine check only as a sanity screen for geospatial input. Real road
travel should use a caller-approved travel-time or distance matrix. Asymmetric
costs are acceptable when the matrix is complete and direction is intentional.

## Minimal REST Sketch

```json
{
  "idempotency_key": "quote-tsp-001",
  "problem_type": "1.1.tsp",
  "problem_schema_version": "1.1.tsp.input.v1",
  "input": {
    "nodes": ["depot", "a", "b"],
    "start_node": "depot",
    "distances": {
      "depot": {"depot": 0, "a": 10, "b": 12},
      "a": {"depot": 10, "a": 0, "b": 4},
      "b": {"depot": 12, "a": 4, "b": 0}
    }
  }
}
```

## Minimal MCP Sketch

```json
{
  "name": "agentsolve.quotes.create",
  "arguments": {
    "idempotency_key": "quote-tsp-001",
    "problem_type": "1.1.tsp",
    "problem_schema_version": "1.1.tsp.input.v1"
  }
}
```

Common pitfalls: repeated cities, missing matrix arcs, accidental asymmetric
costs, using geodesic estimates as if they were travel times, and selecting TSP
when capacity or several routes are central.

For result confidence, see
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
