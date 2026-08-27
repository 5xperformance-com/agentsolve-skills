# Problem Type: TSP

Canonical schema versions:

- Input: `1.1.tsp.input.v1`
- Output: `1.1.tsp.output.v1`

Use `1.1.tsp` when one vehicle or one agent must visit each required node once
and return to the start. Common user wording includes
"route through all stops" and "visit every customer once and return".

For platform transport, pair this file with
[reference-rest-access.md](reference-rest-access.md) or
[reference-mcp-access.md](reference-mcp-access.md), plus
[reference-polling-and-backoff.md](reference-polling-and-backoff.md).

## Formulation Recipe

- Inputs: stable node IDs, a directed distance or cost map, and an optional
  start node. A missing directed edge is unavailable, not zero.
- Objective direction: minimize total route distance or cost.
- Units: keep every matrix entry in the same unit; seconds, minutes, meters,
  miles, and currency costs must not be mixed.
- Normalization: include every node exactly once in the input set; use integer
  scaled costs when source data is decimal.
- Complexity tier bands: `XS` node_count <= 10, `S` 11-25, `M` 26-60,
  `L` 61-2,500. Node count and matrix completeness are the first sizing
  check.
- The schema accepts at most 2,500 nodes. The quote descriptor reports node
  count, directed arc count, and matrix density; the tier itself is not a
  latency or tour-quality guarantee.

## Boundary

If capacity, multiple vehicles, hard arrival windows, pickup/delivery pairing,
split delivery, several depots, soft windows, or time-varying travel is
required, do not force the request into TSP.

Typed deferral guidance:

| Required semantic | Action |
|---|---|
| multiple tours | typed deferral code `tsp_multiple_tours`; consider `1.2.vrp.cvrp` when its route semantics fit |
| capacity | typed deferral code `tsp_capacity_constraints`; consider `1.2.vrp.cvrp` when its route semantics fit |
| hard arrival windows or service times | typed deferral code `tsp_time_windows`; consider the CVRP hard-window subset when all fields fit |
| optional nodes | typed deferral code `tsp_optional_nodes`; the nearest TSP subset visits every node |
| prize collecting | typed deferral code `tsp_prize_collecting`; the nearest TSP subset has no prizes |
| pickup/delivery pairing | reclassify to `1.2.vrp.cvrp` input v4 and declare `pickup_delivery_pairs` per its class reference; pre-v4 CVRP schema versions defer this as `pickup_delivery_vrp` |
| split delivery | code `split_delivery_vrp`, nearest_supported_subset `1.2.vrp.cvrp`, roadmap_status `deferred` |
| several depots | reclassify to `1.2.vrp.cvrp` input v4 and declare `depots` with per-vehicle start/end per its class reference; pre-v4 CVRP schema versions defer this as `multi_depot_vrp` |
| soft windows | reclassify to `1.2.vrp.cvrp` input v4 and declare `soft_time_windows` with priced lateness per its class reference; pre-v4 CVRP schema versions defer this as `soft_time_windows_vrp` |
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
