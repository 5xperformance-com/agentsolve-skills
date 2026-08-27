# Problem Type: Variable-Sized Bin Packing

Canonical schema versions:

- Input: `9.3.bin_packing.input.v3`
- Output: `9.3.bin_packing.output.v2`

Use `9.3.bin_packing` to partition indivisible, positive-integer-size items into
priced bins drawn from one or more bin types, minimizing the total cost of the
bins used, optionally keeping conflicting item pairs in separate bins.

## Formulation Recipe

- `bin_types` is a non-empty list of `{capacity, cost}` bin types, each a
  positive integer capacity (1 through 1,000,000) and a positive integer cost
  (1 through 1,000,000,000). Supply unlimited bins of each type. Use a single
  unit-cost type for ordinary minimum-count packing.
- `items` has 1–1000 unique identifiers.
- `conflicts` is an optional list of two-element item-id pairs that may not
  share a bin (incompatible goods, hazardous-material separation). Omit it for
  ordinary packing.
- Every item must fit the largest bin type; an oversized item is rejected before
  execution. A used bin is priced at the cheapest type that holds its contents.
- The objective is the total cost of the bins used.
- `candidate_bins` is accepted only with `verify_only` and must be an exact
  partition.

## Deferrals

| Required semantic | Action |
|---|---|
| several size dimensions | code `bin_packing_multidimensional`; nearest supported subset has one size |
| item-specific bins | code `bin_packing_item_bin_eligibility`; nearest supported subset lets every item use every bin |
| a limited number of bins of a type | code `bin_packing_limited_bin_supply`; nearest supported subset has unlimited bins of every declared type |
| repeated demand cut from stock lengths | code `bin_packing_cutting_stock`; nearest supported subset packs each declared item once |
| split items | code `bin_packing_splittable_items`; nearest supported subset has indivisible items |
| several objectives | code `bin_packing_multiobjective`; nearest supported subset minimizes total cost |

## Result Interpretation

The verifier checks exact item membership, bin capacity, conflicts, and total
cost. Its exact-proof envelope covers one-bin-type instances through 16 items
and heterogeneous-bin instances through 12 items; that predicate is separate
from the pricing-tier label (`S` item_count <= 16, `M` 17–80,
`L` 81–1,000). Outside the exact-proof envelope,
meeting the exact integer volume lower bound proves the named proposition because
every packing costs at least `ceil(total_size * min(cost / capacity))`. A
reported bound or approximate equality alone does not create a proof.
