# Problem Type: Newsvendor

Canonical schema versions:

- Input: `3.1.newsvendor.input.v1`
- Output: `3.1.newsvendor.output.v1`

Use `3.1.newsvendor` for a single-period inventory or capacity-ordering
decision with explicit discrete demand. The demand uncertainty must be supplied
as a discrete distribution, scenario set, or scenario tree. Do not fit a demand
forecast inside the adoption flow.

## Formulation Recipe

- Decision: one order quantity or capacity quantity for one sale period.
- Inputs: order cost, shortage or underage cost, overage or salvage economics,
  and explicit demand outcomes with probabilities or scenario weights.
- Objective direction: minimize expected cost or maximize expected profit.
- Recompute by summing cost or profit over the explicit demand outcomes.
- Use LP/MILP only when the caller adds linear coupling constraints that are
  genuinely part of the accepted model.

## Deferrals

| Required semantic | Action |
|---|---|
| multi-period inventory policy | code `multi_period_inventory`, nearest_supported_subset `3.1.newsvendor`, roadmap_status `deferred` |
| required service probability or risk constraint | code `chance_constrained_optimization`, nearest_supported_subset expected-value LP/MILP or newsvendor, roadmap_status `deferred` |

Correlated multi-SKU portfolios, censored sales history, tiny scenario samples,
and capacity-coupled SKUs require explicit modelling discussion before payload
drafting. Censored sales are not the same as true demand.

## Result Interpretation

The output cites `3.1.newsvendor.output.v1` and reports the selected quantity
with expected cost or expected profit. For the single-SKU unconstrained case,
the critical fractile is the useful sanity check: order up to the demand
quantile implied by underage cost divided by underage plus overage cost. The
verifier can recompute closed-form or grid evidence over the explicit scenarios.

## Minimal REST Sketch

```json
{
  "idempotency_key": "quote-newsvendor-001",
  "problem_type": "3.1.newsvendor",
  "problem_schema_version": "3.1.newsvendor.input.v1",
  "input": {
    "unit_cost": 5,
    "unit_price": 9,
    "salvage_value": 2,
    "demand_distribution": [
      {"demand": 10, "probability": 0.25},
      {"demand": 20, "probability": 0.50},
      {"demand": 30, "probability": 0.25}
    ]
  }
}
```

## Minimal MCP Sketch

```json
{
  "name": "agentsolve.quotes.create",
  "arguments": {
    "idempotency_key": "quote-newsvendor-001",
    "problem_type": "3.1.newsvendor",
    "problem_schema_version": "3.1.newsvendor.input.v1"
  }
}
```

Common pitfalls: using sales history as uncensored demand, omitting scenario
probabilities, turning a planning horizon into a single-period model without
caller approval, and promising demand-model fitting.

For result confidence, see
[method-stochastic-newsvendor.md](method-stochastic-newsvendor.md)
and [reference-verification-and-certificates.md](reference-verification-and-certificates.md).
