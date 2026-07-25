# Problem Type: MILP

Canonical schema versions:

- Input: `2.2.milp.input.v1`
- Output: `2.2.milp.output.v1`

Use `2.2.milp` when the model is linear and at least one variable is integer or
binary. Keep all modelling in canonical V5 fields.

## Formulation Recipe

- Variables: continuous, integer, and binary variables with explicit bounds.
- Constraints: linear constraints only.
- Objective direction: one linear objective.
- Patterns: fixed charge, set covering, set packing, set partitioning,
  either-or, tight big-M, piecewise-linear convex cost via linear segments, and
  symmetry breaking.
- Scaling: derive big-M values from real bounds; suspiciously huge big-M values
  should become warnings before quote creation.

## Deferrals

- code `quadratic_or_conic_optimization`, nearest_supported_subset linear
  LP/MILP, roadmap_status `deferred`
- code `chance_constrained_optimization`, nearest_supported_subset deterministic
  LP/MILP or accepted expected-value model, roadmap_status `deferred`
- code `native_multi_objective_optimization`, nearest_supported_subset one
  accepted scalar objective, roadmap_status `deferred`
- code `provider_native_payload_required`, nearest_supported_subset canonical
  AgentSolve schema, roadmap_status `not_planned`

## Result Interpretation

The output cites `2.2.milp.output.v1`. Read variable values, objective value,
`best_bound`, `optimality_gap`, incumbent quality, and infeasibility diagnostic
labels `formal_iis`, `conflict_candidate`, and `semantic_diagnostic`.

Optimality certification rule:

```text
optimality_certified = (solver_status == OPTIMAL) AND (optimality_gap <= OPTIMALITY_GAP_CERTIFICATION_TOLERANCE)
```

Do not interpret `TIME_LIMIT` as optimal regardless of the reported gap. A
time-limited incumbent may be useful, but it is not the same as a certified
optimum.

## Minimal REST Sketch

```json
{
  "idempotency_key": "quote-milp-001",
  "problem_type": "2.2.milp",
  "problem_schema_version": "2.2.milp.input.v1",
  "input": {
    "id": "milp-small-001",
    "job_intent": "optimize",
    "variables": {
      "open_a": {"type": "binary"},
      "ship_a": {"type": "integer", "lb": 0}
    },
    "constraints": [
      {
        "id": "capacity_a",
        "function": {
          "type": "linear",
          "coefficients": {"ship_a": 1, "open_a": -50},
          "constant": 0
        },
        "set": {"type": "nonpos"}
      }
    ],
    "objective": {
      "id": "max_margin",
      "sense": "maximize",
      "function": {
        "type": "linear",
        "coefficients": {"open_a": -100, "ship_a": 8},
        "constant": 0
      }
    }
  }
}
```

## Minimal MCP Sketch

```json
{
  "name": "agentsolve.quotes.create",
  "arguments": {
    "idempotency_key": "quote-milp-001",
    "problem_type": "2.2.milp",
    "problem_schema_version": "2.2.milp.input.v1"
  }
}
```

See [method-mixed-integer-linear-programming.md](method-mixed-integer-linear-programming.md)
plus [formulation-patterns.md](formulation-patterns.md),
[infeasibility-diagnostics.md](infeasibility-diagnostics.md), and
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
