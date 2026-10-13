# Problem Type: Minimum-Cost Flow

Canonical schema versions:

- Input: `6.1.min_cost_flow.input.v1`
- Output: `6.1.min_cost_flow.output.v1`

Use `6.1.min_cost_flow` when one commodity moves through a directed network
from nodes that supply it to nodes that demand it, every arc has a capacity
and a per-unit cost, and the goal is the cheapest way to meet every supply and
demand in full: plants to customers through depots, goods through a
transshipment network, a transportation problem with contractual minimum
shipments. Quantities and costs are integers; the answer is exact.

## Formulation Recipe

- Nodes: each node has an `id` and a signed integer `supply`. Positive supply
  is available at the node, negative supply is demand, and zero marks a pure
  transshipment point. The supplies must sum to zero.
- Arcs: each arc has an `id`, a directed `from` and `to` that name declared
  nodes, an integer `lower` (default 0), an integer `upper` with
  `lower <= upper`, and a signed integer `cost` per unit of flow. Parallel arcs
  between the same pair are allowed; an arc from a node to itself is rejected.
- Maximisation: negate the costs. A route that earns revenue per unit gets a
  negative cost, and the objective comes back negated.
- Node capacities: a node that can handle at most `X` units is split into an
  in-node and an out-node joined by one arc with `upper = X`. Arcs that entered
  the node enter the in-node; arcs that left it leave the out-node.
- Minimum shipments: set `lower` on the arc. A contract that guarantees a
  route at least 10 units is `"lower": 10`.
- Complexity tier: arc count selects the catalog band — `S` up to 500 arcs,
  `M` 501–5,000, `L` above 5,000.

## Units and Integers

Every quantity and cost is an integer in declared fixed-precision units.
`units.quantity_decimals` and `units.cost_decimals` (both default 0, at most 6)
say what the integers mean: with `cost_decimals: 2`, a `cost` of `325` is 3.25
per unit, and with `quantity_decimals: 1`, a flow of `25` is 2.5 units. The
objective comes back in the same scaled units: an `objective_value` of `13400`
with two cost decimals is 134.00.

Enter data already scaled. A fractional number such as `3.25` is rejected with
the field named; it is never rounded.

## Deferrals

The quote request answers these with a typed deferral
(`PROBLEM_NOT_SUPPORTED`, `roadmap_status: deferred`) rather than an
approximation:

| Required semantic | Action |
|---|---|
| supplies and demands that do not sum to zero, such as delivering as much as possible when supply falls short | code `flow_supply_demand_imbalance`; nearest supported subset `6.1.min_cost_flow` has balanced supplies and demands. Add a shortfall sink with the missing demand and a penalty cost, and the supplies balance |

Needs that other classes model are not deferrals of this class: several
commodities sharing arcs are a linear program over per-commodity arc
variables (`2.1.lp`), and a fixed charge for using a route needs a binary
decision (`2.2.milp`).

Provider-native payloads fall under deferral code
`provider_native_payload_required`; submit the canonical schema instead.

## Result Interpretation

The output cites `6.1.min_cost_flow.output.v1` and carries `solver_status`,
`objective_value`, `arc_flows` (one integer per arc id), `node_potentials`,
`infeasible_cut`, `optimality_gap`, and `best_bound`. Every answer is checked
in exact integer arithmetic: arc bounds, flow conservation at every node, and
the objective recomputed from the flows.

- `established_guarantee` is `global_optimality` with an
  `independent_certificate` for proposition `min_cost_flow.optimality` when the
  engine returns node potentials that certify its flow: every arc with slack
  below its upper bound has non-negative reduced cost and every arc with slack
  above its lower bound has non-positive reduced cost. The potentials are the
  dual solution, and the check is exact.
- `established_guarantee` is `validity` when the engine returns a flow alone:
  the flow is feasible and its objective is recomputed, but no optimality
  proof accompanies it.
- `established_guarantee` is `infeasibility` with an `independent_certificate`
  for proposition `min_cost_flow.infeasibility` when the engine returns a true
  Hoffman cut in `infeasible_cut`: a set of nodes whose required net outflow
  does not fit the capacity of the arcs that cross its boundary. An infeasible answer
  without a cut is unverified and refunded.
- A flow that breaks a bound or a conservation row, or whose reported
  objective differs from the recomputed one, is unverified and refunded.
- Several optimal flows can tie. Any flow whose potentials pass is accepted;
  the verifier does not compare it with a reference flow.

## Minimal REST Sketch

```json
{
  "idempotency_key": "quote-min-cost-flow-001",
  "problem_type": "6.1.min_cost_flow",
  "problem_schema_version": "6.1.min_cost_flow.input.v1",
  "input": {
    "id": "mcf-small-001",
    "nodes": [
      {"id": "plant", "supply": 7},
      {"id": "depot", "supply": 0},
      {"id": "shop", "supply": -7}
    ],
    "arcs": [
      {"id": "plant_depot", "from": "plant", "to": "depot", "upper": 10, "cost": 1},
      {"id": "depot_shop", "from": "depot", "to": "shop", "upper": 10, "cost": 1},
      {"id": "plant_shop", "from": "plant", "to": "shop", "lower": 2, "upper": 4, "cost": 5}
    ],
    "units": {"quantity_decimals": 0, "cost_decimals": 0}
  }
}
```

## Minimal MCP Sketch

```json
{
  "name": "agentsolve.quotes.create",
  "arguments": {
    "idempotency_key": "quote-min-cost-flow-001",
    "problem_type": "6.1.min_cost_flow",
    "problem_schema_version": "6.1.min_cost_flow.input.v1"
  }
}
```

See [formulation-patterns.md](formulation-patterns.md),
[infeasibility-diagnostics.md](infeasibility-diagnostics.md), and
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
