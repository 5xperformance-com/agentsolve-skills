# Method: Mixed-Integer Linear Programming

Use this for linear models with binary or integer variables. For payload
details, see [problem-type-milp.md](problem-type-milp.md).

## Math Contract

The verifier checks constraint validity and objective recomputation. Backend
metadata may include `solver_status`, `best_bound`, `optimality_gap`, and
`optimality_certified`.

```text
optimality_certified = (solver_status == OPTIMAL) AND (optimality_gap <= OPTIMALITY_GAP_CERTIFICATION_TOLERANCE)
```

## Time Limits And Bounds

`TIME_LIMIT` means the solver stopped before certified optimality. The incumbent
may be useful, but agents must report the bound and gap plainly. `best_bound`
has the same objective sense as the public result and is the basis for gap
interpretation.

## Formulation Discipline

Prefer tight formulations, finite bounds, and big-M values derived from real
limits. LP-relaxation tightness matters. Cut-family language is useful only as
general method context; Stage 0 exposes no public warm-start payload, and warm
starts are internal adapter behavior until a later schema says otherwise.

See [formulation-patterns.md](formulation-patterns.md) and
[infeasibility-diagnostics.md](infeasibility-diagnostics.md).
