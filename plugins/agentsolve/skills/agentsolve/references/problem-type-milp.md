# Problem Type: MILP

Canonical schema versions:

- Input: `2.2.milp.input.v2`
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
- Variable count selects the catalog band — `S` <= 25, `M` 26–100,
  `L` 101–10,000; constraints are capped at 50,000. Use the quote descriptor's
  nonzeros, density, integrality density, numeric magnitude spans, and
  tolerance exponent to interpret measured evidence.

## Out-Of-Scope Boundaries

`2.2.milp` accepts one scalar linear objective over continuous and integer
variables. The requests below are out of scope; the ROADMAP reserves
typed-deferral codes for them, but the current runtime rejects such
payloads at schema validation (`SCHEMA_VALIDATION`) without emitting the
codes — screen for these needs before quoting rather than waiting for a
typed deferral:

- deferral code `quadratic_or_conic_optimization` — quadratic or conic terms
- deferral code `native_multi_objective_optimization` — native
  multi-objective frontiers
- deferral code `provider_native_payload_required` — provider-native
  payloads; submit the canonical schema instead Weighted-sum
single-objective LP/MILP reformulation is allowed when the caller accepts
fixed weights; goal-programming single-objective LP/MILP reformulation is
allowed with accepted deviation penalties; expected-value modelling is
allowed when the caller accepts it.

## Result Interpretation

The output cites `2.2.milp.output.v1`. Read variable values, objective value,
`best_bound`, `optimality_gap`, incumbent quality, and infeasibility diagnostic
labels `formal_iis`, `conflict_candidate`, and `semantic_diagnostic`.

The verifier independently checks variable identity, bounds, integrality,
constraints, and objective recomputation. That establishes `valid_result`,
not global optimality. `solver_proved` requires an explicit admitted-adapter
proof signal with terminal `OPTIMAL`. A raw `optimality_certified` flag, zero
gap, equal bound, or rounded value is diagnostic and cannot create the claim.
A time-limited valid incumbent may settle as feasible without a proof.
That result can carry `established_guarantee=validity` even when exact
optimality is not tractable.

## Minimal REST Sketch

```json
{
  "idempotency_key": "quote-milp-001",
  "problem_type": "2.2.milp",
  "problem_schema_version": "2.2.milp.input.v2",
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
    "problem_schema_version": "2.2.milp.input.v2"
  }
}
```

See [method-mixed-integer-linear-programming.md](method-mixed-integer-linear-programming.md)
plus [formulation-patterns.md](formulation-patterns.md),
[infeasibility-diagnostics.md](infeasibility-diagnostics.md), and
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
