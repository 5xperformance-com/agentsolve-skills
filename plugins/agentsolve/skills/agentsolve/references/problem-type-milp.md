# Problem Type: MILP

Contents: Customer Phrasing · Formulation Recipe · Out-Of-Scope Boundaries · Result Interpretation · Minimal REST Sketch

Canonical schema versions:

- Input: `2.2.milp.input.v2`
- Output: `2.2.milp.output.v1`

Use `2.2.milp` when the model is linear and at least one variable is integer or
binary. Keep all modelling in canonical fields.

## Customer Phrasing

| Customer phrasing | Decision | Notes |
|---|---|---|
| "choose which warehouse opens" | `2.2.milp` | Binary open decisions make it MILP. |
| "our feasibility tolerance is looser than the default" | `2.2.milp` input v2 | Declare `metadata.feasibility_tolerance`; v2 hashes it and the verifier judges at the value you declared. |

## Formulation Recipe

- Variables: continuous and integer variables with explicit bounds. A binary
  variable takes no bounds: it is 0 or 1 by definition, and a bound on one is
  refused.
- Constraints: linear constraints only.
- Objective direction: one linear objective.
- Patterns: fixed charge, set covering, set packing, set partitioning,
  either-or, tight big-M, piecewise-linear convex cost via linear segments, and
  symmetry breaking.
- Scaling: derive big-M values from real bounds; suspiciously huge big-M values
  should become warnings before quote creation.
- Variable count selects the size tier — `S` <= 25, `M` 26–100,
  `L` 101–10,000; constraints are capped at 50,000. Use the quote descriptor's
  nonzeros, density, integrality density, numeric magnitude spans, and
  tolerance exponent to interpret measured evidence.

## Out-Of-Scope Boundaries

`2.2.milp` accepts one scalar linear objective over continuous and integer
variables. The requests below are out of scope and carry no typed deferral:
the API rejects such payloads with `INVALID_PAYLOAD`. Screen for these needs
before quoting:

- quadratic or conic terms
- native multi-objective frontiers
- solver-native payloads; submit the canonical schema instead

Weighted-sum single-objective LP/MILP reformulation is allowed when the
caller accepts fixed weights; goal-programming single-objective LP/MILP
reformulation is allowed with accepted deviation penalties; expected-value
modelling is allowed when the caller accepts it.

## Result Interpretation

The output cites `2.2.milp.output.v1`. Read variable values, objective value,
`best_bound`, `optimality_gap`, and incumbent quality. When the verifier
rejects a result, `infeasibility_diagnostic` carries the label
`semantic_diagnostic` and the verifier's reason.

The verifier independently checks variable identity, bounds, integrality,
constraints, and objective recomputation. That establishes `valid_result`,
not global optimality. `solver_proved` requires the engine's own explicit
proof signal: a terminal `OPTIMAL` status with the gap closed. A raw
`optimality_certified` flag, zero gap, equal bound, or rounded value is
diagnostic and cannot create the claim.
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
  },
  "policy": {"max_price_usdc": "0.50"}
}
```

Over MCP, pass the same object as the `arguments` of
`agentsolve.quotes.create`.

See [method-mixed-integer-linear-programming.md](method-mixed-integer-linear-programming.md)
plus [formulation-patterns.md](formulation-patterns.md),
[infeasibility-diagnostics.md](infeasibility-diagnostics.md), and
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
