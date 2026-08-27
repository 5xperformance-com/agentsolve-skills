# Problem Type: Bounded Knapsack

Canonical schema versions:

- Input: `9.1.knapsack.input.v2`
- Output: `9.1.knapsack.output.v1`

Use `9.1.knapsack` to choose indivisible items maximizing exact integer value
under one exact integer capacity, taking each item up to its quantity bound.

## Formulation Recipe

- `capacity` is from 0 through 75,000.
- `items` has 1–2,500 unique identifiers.
- Weight is positive; value is non-negative.
- `quantity` is an optional positive integer (default 1) capping how many copies
  of an item may be chosen. Omit it for ordinary 0/1 selection.
- An overweight item is valid but cannot be selected.
- The empty set is always feasible, so the class has no infeasible result.
- A chosen item appears once per copy in `selected_item_ids`, so the selection
  is a sorted multiset; a pure single-copy instance produces a plain set.

## Deferrals

| Required semantic | Action |
|---|---|
| several capacity dimensions | code `knapsack_multi_capacity`; nearest supported subset has one capacity |
| several containers | code `knapsack_multiple_containers`; nearest supported subset has one knapsack |
| fractional selection | code `knapsack_fractional_items`; nearest supported subset has indivisible items |
| prerequisites or conflicts | code `knapsack_dependencies`; nearest supported subset has independent items |
| staged projects with period budgets or prerequisites | code `knapsack_project_portfolio`; nearest supported subset selects independent items under one capacity |
| uncertain data | code `knapsack_uncertain_values`; nearest supported subset has fixed values and weights |
| several objectives | code `knapsack_multiobjective`; nearest supported subset maximizes one value |

## Result Interpretation

The verifier always checks selected identifiers, capacity, total weight, and
total value with exact integers. When the bounded dynamic-program work
(binary-decomposed copies × `(capacity + 1)`) is at most 1,000,000, optimize
results also receive a separate exact optimum-value check.
Any feasible selection tied at that value is accepted; the verifier does not
require the same witness. Pricing tiers band on the same bounded DP work:
`S` <= 1,000,000, `M` to 20,000,000, `L` to 187,502,500.

Above that work cap, validity and objective are independent checks, while
global optimality remains solver-sourced and requires an explicit proof signal.
`verify_only` never invokes the optimum recomputation.
