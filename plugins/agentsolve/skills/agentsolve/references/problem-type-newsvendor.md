# Problem Type: Newsvendor

Contents: Customer Phrasing · Formulation Recipe · Deferrals · Result Interpretation · Minimal REST Sketch

Canonical schema versions:

- Input: `3.1.newsvendor.input.v1`
- Output: `3.1.newsvendor.output.v2`

Use `3.1.newsvendor` for a single-period inventory or capacity-ordering
decision with explicit discrete demand. The demand uncertainty must be supplied
as a flat list of demand scenarios for each item. Do not fit a demand
forecast inside the adoption flow.

## Customer Phrasing

| Customer phrasing | Decision | Notes |
|---|---|---|
| "how many units should we stock for one sale period" | `3.1.newsvendor` | Explicit independent discrete SKU scenarios. |
| "inventory policy over the next 12 months" | typed deferral `multi_period_inventory` | One static ordering period only. |
| "SKUs share one purchasing budget" | typed deferral `capacity_coupled_inventory` | SKU decisions are independent. |
| "demand is correlated across products" | typed deferral `correlated_inventory` | Scenarios are per SKU. |

## Formulation Recipe

- Decision: one order quantity or capacity quantity for one sale period.
- Inputs: order cost, shortage or underage cost, overage or salvage economics,
  and explicit demand outcomes, each with a probability; one item's
  probabilities must sum to 1.
- Objective direction: minimize expected cost or maximize expected profit.
- Recompute by summing cost or profit over the explicit demand outcomes.
- Use LP/MILP only when the caller adds linear coupling constraints that are
  genuinely part of the accepted model.
- S means at most 2 SKUs and 16 total scenarios; M means outside S but at most
  8 SKUs and 64 total scenarios; larger schema-valid inputs are L. The schema
  caps SKUs at 2,500 and scenarios at 10,000 per SKU. Inspect
  `order_grid_work` for performance evidence.

## Deferrals

| Required semantic | Action |
|---|---|
| multi-period inventory policy | code `multi_period_inventory`, nearest_supported_subset `3.1.newsvendor`, roadmap_status `deferred` |
| required service probability or risk constraint | code `chance_constrained_optimization`, nearest_supported_subset expected-value LP/MILP or newsvendor, roadmap_status `deferred` |
| SKUs sharing one budget or capacity | code `capacity_coupled_inventory`, nearest_supported_subset independent SKU decisions, roadmap_status `deferred` |
| demand correlated across SKUs | code `correlated_inventory`, nearest_supported_subset independent per-SKU scenarios, roadmap_status `deferred` |
| an ambiguity set in place of one demand distribution | code `distributionally_robust_inventory`, nearest_supported_subset an explicit discrete demand distribution, roadmap_status `deferred` |
| a rolling reorder policy | code `rolling_inventory_policy`, nearest_supported_subset one static order decision, roadmap_status `deferred` |

Correlated multi-SKU portfolios, censored sales history, tiny scenario samples,
and capacity-coupled SKUs require explicit modelling discussion before payload
drafting. Censored sales are not the same as true demand.

## Result Interpretation

The output cites `3.1.newsvendor.output.v2` and reports the selected quantity
with expected cost or expected profit. For the single-SKU unconstrained case,
the critical fractile is the useful sanity check: order up to the demand
quantile implied by underage cost divided by underage plus overage cost. The
verifier recomputes the expected objective over the explicit scenarios. When
`order_grid_work` (order-grid points times scenarios, summed over SKUs) is at
most 1,000,000, it also enumerates the order grid exactly: a result that
matches the optimum gets an exact rational certificate, and a result that
claims `OPTIMAL` but falls short is unverified and refunded. Above that cap,
or when the exact enumeration runs out of its own budget, a result is
certified valid, not optimal.

## Minimal REST Sketch

```json
{
  "idempotency_key": "quote-newsvendor-001",
  "problem_type": "3.1.newsvendor",
  "problem_schema_version": "3.1.newsvendor.input.v1",
  "input": {
    "id": "newsvendor-small-001",
    "objective": "max_expected_profit",
    "items": [
      {
        "sku_id": "sku_1",
        "unit_cost": 5,
        "selling_price": 9,
        "salvage_value": 2,
        "max_order_qty": 40,
        "demand_scenarios": [
          {"demand_qty": 10, "probability": 0.25},
          {"demand_qty": 20, "probability": 0.50},
          {"demand_qty": 30, "probability": 0.25}
        ]
      }
    ]
  },
  "policy": {"max_price_usdc": "0.50"}
}
```

Over MCP, pass the same object as the `arguments` of
`agentsolve.quotes.create`.

Common pitfalls: using sales history as uncensored demand, omitting scenario
probabilities, turning a planning horizon into a single-period model without
caller approval, and promising demand-model fitting.

For result confidence, see
[method-stochastic-newsvendor.md](method-stochastic-newsvendor.md)
and [reference-verification-and-certificates.md](reference-verification-and-certificates.md).
