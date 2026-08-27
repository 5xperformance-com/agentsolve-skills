# Problem Type: Weighted Set Cover

Canonical schema versions:

- Input: `9.2.set_cover.input.v3`
- Output: `9.2.set_cover.output.v1`

Use `9.2.set_cover` to choose a minimum-total-cost subset of submitted sets so
that every submitted element is covered at least its required number of times,
or is left short at a declared per-unit penalty.

## Formulation Recipe

- `elements` has 1–2,500 unique identifiers. Each element may carry an integer
  `demand` from 1 through 1,000,000 (default 1) — the least number of selected
  sets that must contain it. Omit it for ordinary single cover.
- Each element may carry an integer `uncovered_penalty` from 0 through
  1,000,000,000 — the cost charged per unit of unmet demand when the element is
  left short. Omit it to make the element a hard cover that must be fully met.
- `sets` has 1–10,000 unique identifiers, non-negative integer costs, and
  non-empty coverage lists.
- Every hard-cover element must occur in at least `demand` submitted sets; a
  penalized element may occur in fewer (its shortfall is priced, not rejected).
- The objective is total set cost plus every element's unmet demand priced at
  its `uncovered_penalty`.
- Total set-element incidence is capped at 250,000. Pricing tiers band on
  set count: `S` <= 20, `M` 21–1,000, `L` 1,001–10,000.
- `candidate_set_ids` is accepted only with `verify_only`.

## Deferrals

| Required semantic | Action |
|---|---|
| set capacities | code `set_cover_capacitated`; nearest supported subset is uncapacitated |
| set interactions | code `set_cover_set_interactions`; nearest supported subset has additive costs |
| coverage rules based on distance, radius, or a service level | code `set_cover_service_constraints`; nearest supported subset states set membership explicitly |
| one element's coverage substituting for another's | code `set_cover_element_interactions`; nearest supported subset treats elements independently |
| uncertain costs or coverage | code `set_cover_uncertain_costs`; nearest supported subset has fixed data |
| several objectives | code `set_cover_multiobjective`; nearest supported subset minimizes one cost |

## Result Interpretation

The verifier recomputes coverage and exact integer total cost, including every
uncovered penalty. This establishes `valid_result`, not an independent global optimum.
A specialist incumbent or lower bound remains diagnostic; only an explicit
admitted-solver optimal signal can create `solver_proved`.
