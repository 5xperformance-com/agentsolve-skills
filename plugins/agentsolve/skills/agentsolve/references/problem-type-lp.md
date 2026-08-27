# Problem Type: LP

Canonical schema versions:

- Input: `2.1.lp.input.v2`
- Output: `2.1.lp.output.v2`

Use `2.1.lp` for continuous decision variables with a linear objective and
linear constraints. The adoption surface teaches the canonical V5 payload only.

## Formulation Recipe

- Variables: continuous variables with finite bounds where the business domain
  provides them.
- Accuracy: `metadata.feasibility_tolerance` declares how exactly constraints
  must hold for the answer to be called valid. It defaults to `1e-8` and is
  accepted in the band `[1e-9, 1e-3]`. It is not a hint: the verifier judges
  against it, and it changes the canonical problem hash. Ask for a looser
  tolerance only when a looser answer is genuinely acceptable, because it
  widens which engines are eligible.
- Constraints: linear equalities or inequalities with explicit coefficients.
- Objective direction: minimize or maximize one linear objective.
- Units and scaling: keep coefficients in compatible units; avoid large
  coefficient ranges when a simple unit conversion fixes them.
- Complexity tier: variable count selects the catalog band — `S` <= 25,
  `M` 26–100, `L` 101–10,000. The schema also caps constraints at 50,000. Inspect the
  descriptor's constraint count, nonzeros, density, numeric magnitude spans,
  and tolerance exponent before relying on measured performance evidence.

## Out-Of-Scope Boundaries

`2.1.lp` accepts one scalar linear objective over continuous variables.
The requests below are out of scope; the ROADMAP reserves typed-deferral
codes for them, but the current runtime rejects such payloads at schema
validation (`SCHEMA_VALIDATION`) without emitting the codes — screen for
these needs before quoting rather than waiting for a typed deferral:

- deferral code `quadratic_or_conic_optimization` — quadratic or conic terms
- deferral code `native_multi_objective_optimization` — native
  multi-objective frontiers
- deferral code `provider_native_payload_required` — provider-native
  payloads; submit the canonical schema instead

Weighted-sum single-objective LP/MILP reformulation is allowed when
the caller accepts fixed weights. Goal-programming single-objective LP/MILP
reformulation is allowed with accepted deviation penalties.

## Result Interpretation

The output cites `2.1.lp.output.v2`. Read variable values, objective value,
primal feasibility, dual values where populated, reduced-cost availability,
unbounded or infeasible status, and receipt fields such as
`engine_library_version`, `engine_capability_fingerprint`, `solver_status`,
`optimality_gap`, and `best_bound`. Dual values and reduced costs are useful
sensitivity signals when present; they are not guaranteed on every result.
For an infeasible result, `variable_values` may be null and `dual_ray` carries
the row multipliers used by the verifier's exact Farkas check. The receipt
reports `INFEASIBILITY` only when that check succeeds.

Network-flow, transportation, assignment, and transshipment structures may
produce integer-looking solutions without a MILP when the linear structure is
sufficient.

## Minimal REST Sketch

```json
{
  "idempotency_key": "quote-lp-001",
  "problem_type": "2.1.lp",
  "problem_schema_version": "2.1.lp.input.v2",
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
    "problem_schema_version": "2.1.lp.input.v2"
  }
}
```

See [method-linear-programming.md](method-linear-programming.md),
[formulation-patterns.md](formulation-patterns.md),
[infeasibility-diagnostics.md](infeasibility-diagnostics.md), and
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
