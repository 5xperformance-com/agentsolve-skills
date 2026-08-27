# Problem Type: Unit-Demand Assignment

Canonical schema versions:

- Input: `5.1.assignment.input.v1`
- Output: `5.1.assignment.output.v1`

Use `5.1.assignment` for sparse capacitated bipartite assignment where every
task consumes one unit of agent capacity and every allowed pair carries an
exact integer cost or value.

## Formulation Recipe

- `agents` have integer `capacity`.
- `tasks` are required by default; optional tasks may remain unassigned.
- `pairs` is the complete eligibility relation. An absent pair is forbidden.
- `fixed_assignments` must name allowed pairs and force those selections.
- `sense` is `min` or `max`; weights may be negative.
- Agents, tasks, and pairs are each capped at 100,000 entries. Pricing
  tiers band on allowed pair count: `S` <= 2,500, `M` 2,501–50,000,
  `L` 50,001–100,000.

If decimal business values are required, choose and record an integer scale
before submission. Receipts report the submitted integer unit.

## Deferrals

| Required semantic | Action |
|---|---|
| task demand above one | code `assignment_multi_unit_demand`; nearest supported subset uses unit tasks |
| per-pair resource consumption | code `assignment_gap_consumption`; nearest supported subset consumes one capacity unit |
| preference-list stability | code `assignment_stable_matching`; nearest supported subset uses pair weights |
| pairwise interactions | code `assignment_quadratic_interaction`; nearest supported subset has additive pair weights |

## Result Interpretation

The verifier always checks pair eligibility, task coverage, fixed assignments,
capacities, and the exact integer objective.

For an accepted `optimal` optimize result, it independently solves exact
min-cost flow and checks an exact dual certificate. For an accepted
`infeasible` result, it produces a deficiency cut whose task-set cardinality
exceeds its neighborhood capacity. A merely feasible or `verify_only` result
has validity and exact objective evidence without an optimality certificate.

A public proof flag, zero gap, or objective equality cannot create a proof.
