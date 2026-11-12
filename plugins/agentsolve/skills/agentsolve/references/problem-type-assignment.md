# Problem Type: Unit-Demand Assignment

Canonical schema versions:

- Input: `5.1.assignment.input.v1`
- Output: `5.1.assignment.output.v1`

Use `5.1.assignment` for sparse capacitated bipartite assignment where every
task consumes one unit of agent capacity and every allowed pair carries an
exact integer cost or value.

## Customer Phrasing

| Customer phrasing | Decision | Notes |
|---|---|---|
| "assign these unit tasks to people or machines" | `5.1.assignment` | Sparse allowed pairs and integer weights. |
| "each task consumes a different amount of worker time" | typed deferral `assignment_gap_consumption` | v1 consumes one capacity unit per task. |
| "one task needs three people" | typed deferral `assignment_multi_unit_demand` | Tasks are indivisible and unit demand. |
| "match residents to hospitals by preference lists" | typed deferral `assignment_stable_matching` | Weight optimization does not prove stability. |
| "seat guests so compatible pairs sit together" | typed deferral `assignment_quadratic_interaction` | Pairwise interactions are quadratic. |

## Formulation Recipe

- `agents` have integer `capacity`.
- `tasks` are required by default; a task with `required: false` is optional
  and may remain unassigned.
- `pairs` is the complete eligibility relation. An absent pair is forbidden.
- `fixed_assignments` must name allowed pairs and force those selections.
- `sense` is `min` or `max`; weights may be negative.
- Agents, tasks, and pairs are each capped at 100,000 entries. Size tiers
  follow the allowed pair count: `S` <= 2,500, `M` 2,501–50,000,
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
| minimum loads, quotas, or balance across agents | code `assignment_workload_balance`; nearest supported subset uses agent capacity as an upper bound only |
| a price for leaving a task unassigned | code `assignment_unassigned_penalty`; nearest supported subset lets an optional task go unassigned at no cost |

## Result Interpretation

The verifier always checks pair eligibility, task coverage, fixed assignments,
capacities, and the exact integer objective.

For an accepted `optimal` optimize result inside its work cap, it
independently solves exact min-cost flow and checks an exact dual certificate.
The cap is 50,000,000 on tasks × (agents + tasks + pairs). Above the cap the
result is certified valid, not optimal. For an accepted
`infeasible` result, it produces a deficiency cut whose task-set cardinality
exceeds its neighborhood capacity. A merely feasible or `verify_only` result
has validity and exact objective evidence without an optimality certificate.
`verify_only` needs `candidate_assignment`, the `{agent_id, task_id}` pairs to
check.

A public proof flag, zero gap, or objective equality cannot create a proof.
