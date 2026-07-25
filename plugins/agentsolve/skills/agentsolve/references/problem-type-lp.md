# Problem Type: LP

Canonical schema versions:

- Input: `2.1.lp.input.v1`
- Output: `2.1.lp.output.v1`

Use `2.1.lp` for continuous decision variables with a linear objective and
linear constraints. The adoption surface teaches the canonical V5 payload only.

## Formulation Recipe

- Variables: continuous variables with finite bounds where the business domain
  provides them.
- Constraints: linear equalities or inequalities with explicit coefficients.
- Objective direction: minimize or maximize one linear objective.
- Units and scaling: keep coefficients in compatible units; avoid large
  coefficient ranges when a simple unit conversion fixes them.
- Complexity tier: use variable count, constraint count, and nonzero count.

## Deferrals

Use typed deferral guidance when the request requires:

- code `quadratic_or_conic_optimization`, nearest_supported_subset linear
  LP/MILP, roadmap_status `deferred`
- code `chance_constrained_optimization`, nearest_supported_subset deterministic
  LP/MILP or accepted expected-value model, roadmap_status `deferred`
- code `native_multi_objective_optimization`, nearest_supported_subset one
  accepted scalar objective, roadmap_status `deferred`
- code `provider_native_payload_required`, nearest_supported_subset canonical
  AgentSolve schema, roadmap_status `not_planned`

Weighted-sum single-objective LP/MILP reformulation per ASB-707 is allowed when
the caller accepts fixed weights. Goal-programming single-objective LP/MILP
reformulation per ASB-707 is allowed with accepted deviation penalties.

## Result Interpretation

The output cites `2.1.lp.output.v1`. Read variable values, objective value,
primal feasibility, dual values where populated, reduced-cost availability,
unbounded or infeasible status, and receipt fields such as
`engine_library_version`, `engine_capability_fingerprint`, `solver_status`,
`optimality_gap`, and `best_bound`. Dual values and reduced costs are useful
sensitivity signals when present; they are not guaranteed on every result.

Network-flow, transportation, assignment, and transshipment structures may
produce integer-looking solutions without a MILP when the linear structure is
sufficient.

## Minimal REST Sketch

```json
{
  "idempotency_key": "quote-lp-001",
  "problem_type": "2.1.lp",
  "problem_schema_version": "2.1.lp.input.v1",
  "input": {
    "id": "lp-small-001",
    "variables": {
      "x": {"type": "continuous", "lb": 0},
      "y": {"type": "continuous", "lb": 0}
    },
    "constraints": [
      {
        "id": "demand",
        "function": {
          "type": "linear",
          "coefficients": {"x": 1, "y": 1},
          "constant": -10
        },
        "set": {"type": "nonneg"}
      }
    ],
    "objective": {
      "id": "min_cost",
      "sense": "minimize",
      "function": {
        "type": "linear",
        "coefficients": {"x": 3, "y": 4},
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
    "idempotency_key": "quote-lp-001",
    "problem_type": "2.1.lp",
    "problem_schema_version": "2.1.lp.input.v1"
  }
}
```

See [method-linear-programming.md](method-linear-programming.md),
[formulation-patterns.md](formulation-patterns.md),
[infeasibility-diagnostics.md](infeasibility-diagnostics.md), and
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
