# Problem Type: Convex QP

Canonical schema versions:

- Input: `2.3.qp.input.v1`
- Output: `2.3.qp.output.v1`

Use `2.3.qp` for continuous decision variables with a convex quadratic
objective and linear constraints: a variance or spread to minimize, a
least-squares fit to targets, or a quadratic smoothing penalty over a linear
model. Variables, constraint rows, and metadata use the `2.1.lp` vocabulary;
only the objective function differs. A model with no quadratic term belongs in
`2.1.lp`, whose verifier judges optimality by duality checks within the
declared tolerance.

## Formulation Recipe

- Variables: continuous variables with finite bounds where the domain provides
  them.
- Constraints: linear equalities or inequalities in the `2.1.lp` row shape.
- Objective: `"type": "quadratic"` with `quadratic_terms` (a list of
  `{"x", "y", "coeff"}` monomials), `linear_terms`, and `constant`. The
  objective value is literally
  `Σ coeff·x·y + Σ linear_terms·x + constant`.
- Each unordered pair appears once. Listing both `{"x": "a", "y": "b"}` and
  `{"x": "b", "y": "a"}`, or repeating a pair, is rejected at schema validation
  with the pair named; it is never summed. Terms name declared variables only.
- Direction: `minimize` needs a positive-semidefinite quadratic part and
  `maximize` a negative-semidefinite one. Convexity is decided once, when the
  payload is normalized, within a published tolerance `δ`: `1e-9` times the
  larger of 1 and the largest diagonal magnitude of `M`.
- Enter a singular (semidefinite) matrix at full precision. Rounding its
  entries one by one can push it slightly indefinite, and the convexity check
  then refuses it.
- Accuracy: `metadata.feasibility_tolerance` declares how exactly constraints
  and optimality conditions must hold for the answer to be called valid. It
  defaults to `1e-6` and is accepted in the band `[1e-9, 1e-3]`. It is not a
  hint: the verifier judges against it, and it changes the canonical problem
  hash.
- Complexity tier: variable count selects the catalog band — `S` <= 25,
  `M` 26–100, `L` 101–10,000. The schema also caps constraints at 50,000 and
  quadratic terms at 250,000, and the quadratic terms may span at most 2,000
  distinct variables. The descriptor adds `quadratic_term_count`,
  `quadratic_support_count`, and `quadratic_coefficient_magnitude_span` to the
  linear features.

## Coefficient Convention

`coeff` is the full polynomial coefficient of the monomial `x·y`; `x == y`
gives `coeff·x²`. In matrix form the objective is `xᵀMx + cᵀx + d` with `M`
symmetric, `M[i,i] = coeff_ii` and `M[i,j] = M[j,i] = coeff_ij / 2`. A
covariance `Σ` therefore enters as `coeff_ii = Σ_ii` and `coeff_ij = 2·Σ_ij`,
each pair once.

Worked example: two ingredient shares `a` and `b` whose energy content varies
from delivery to delivery with covariance

```text
Σ = [[0.04,  0.006],
     [0.006, 0.09 ]]
```

The blend's variance is `xᵀΣx = 0.04a² + 2·0.006ab + 0.09b²`, so the terms are:

```json
[
  {"x": "a", "y": "a", "coeff": 0.04},
  {"x": "a", "y": "b", "coeff": 0.012},
  {"x": "b", "y": "b", "coeff": 0.09}
]
```

Entering `0.006` for the cross term would halve the covariance. A least-squares
objective `‖Nx − t‖²` expands the same way: `coeff_ii = (NᵀN)_ii`,
`coeff_ij = 2·(NᵀN)_ij`, `linear_terms = −2·Nᵀt`, and `constant = tᵀt`.

## Deferrals

The quote request answers these with a typed deferral
(`PROBLEM_NOT_SUPPORTED`, `roadmap_status: deferred`) rather than an
approximation:

| Required semantic | Action |
|---|---|
| integer or binary decisions, including a limit on how many options may be used or a fixed charge for using one | code `quadratic_integer_variables`; nearest supported subset `2.3.qp` has continuous variables |
| an objective that is not convex in its direction (indefinite, or concave under `minimize`) | code `nonconvex_quadratic_objective`; nearest supported subset `2.3.qp` has a convex objective |
| a quadratic term inside a constraint row | code `quadratic_constraint`; nearest supported subset `2.3.qp` has linear rows |

Two further needs are out of scope for every schema, so screen for them before
quoting and return the deferral yourself:

- deferral code `quadratic_or_conic_optimization` — conic rows or ellipsoidal
  uncertainty sets
- deferral code `native_multi_objective_optimization` — native
  multi-objective frontiers

Provider-native payloads fall under deferral code
`provider_native_payload_required`; submit the canonical schema instead.

## Result Interpretation

The output cites `2.3.qp.output.v1` and has the shape of
`2.1.lp.output.v2`: `solver_status`, `objective_value`, `variable_values`,
`dual_values`, `reduced_costs`, `dual_ray`, `optimality_gap`, and `best_bound`.
`dual_values` carry one multiplier per constraint row in the `2.1.lp` sign
convention: in the minimization orientation, `nonneg` rows are non-positive,
`nonpos` rows non-negative, and `zeros` rows free.

- `established_guarantee` is `global_optimality` when the KKT conditions hold
  within the declared tolerance: primal feasibility, objective recomputation,
  dual signs, stationarity of the objective's gradient against the returned
  multipliers, and complementary slackness. Stationarity is judged at a
  tolerance scaled by the gradient and by the net contribution of the
  multipliers, so multipliers that cancel one another on repeated rows buy no
  extra slack. For a convex program these conditions establish a global
  optimum, but only within that tolerance: the guarantee is a tolerance
  envelope, not an exact certificate, so no `independent_certificate` is
  issued for it.
- That guarantee is exact for a positive-semidefinite quadratic part. A
  matrix accepted inside the convexity tolerance `δ` can curve slightly
  downward along some direction; a verified point is then optimal only up to
  `δ·D²`, where `D` is the diameter of the feasible region, and if the region
  is unbounded along that direction (a free variable with a slightly negative
  square term) the program may have no minimum at all. Bound the variables
  that carry quadratic terms when the matrix is only semidefinite to rounding.
- The check needs the multipliers. A point returned without `dual_values`, or
  whose multipliers fail stationarity, is unverified and refunded even when it
  is feasible.
- Infeasibility is certified exactly: when the engine supplies a Farkas ray in
  `dual_ray`, the verifier checks it in exact rational arithmetic and reports
  `established_guarantee=infeasibility` with proposition `qp.infeasibility`.
  A missing or refuted ray is unverified and refunded.
- An `unbounded` engine status is refunded as unverified; this version has no
  primal-ray check.
- A singular quadratic form can have a whole face of optimal points. Any point
  whose multipliers pass is accepted; the verifier does not compare it with a
  reference point.

## Minimal REST Sketch

```json
{
  "idempotency_key": "quote-qp-001",
  "problem_type": "2.3.qp",
  "problem_schema_version": "2.3.qp.input.v1",
  "input": {
    "id": "qp-small-001",
    "variables": {
      "a": {"type": "continuous", "lb": 0, "ub": 1},
      "b": {"type": "continuous", "lb": 0, "ub": 1}
    },
    "constraints": [
      {
        "id": "one_batch",
        "function": {
          "type": "linear",
          "coefficients": {"a": 1, "b": 1},
          "constant": -1
        },
        "set": {"type": "zeros"}
      }
    ],
    "objective": {
      "id": "min_blend_variance",
      "sense": "minimize",
      "function": {
        "type": "quadratic",
        "quadratic_terms": [
          {"x": "a", "y": "a", "coeff": 0.04},
          {"x": "a", "y": "b", "coeff": 0.012},
          {"x": "b", "y": "b", "coeff": 0.09}
        ],
        "linear_terms": {},
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
    "idempotency_key": "quote-qp-001",
    "problem_type": "2.3.qp",
    "problem_schema_version": "2.3.qp.input.v1"
  }
}
```

See [method-linear-programming.md](method-linear-programming.md),
[formulation-patterns.md](formulation-patterns.md),
[infeasibility-diagnostics.md](infeasibility-diagnostics.md), and
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
