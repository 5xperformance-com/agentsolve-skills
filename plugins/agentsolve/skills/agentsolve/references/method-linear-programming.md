# Method: Linear Programming

Use this when the user describes continuous allocation, blending or
production. Assignment goes to `5.1.assignment` and single-commodity network
flow to `6.1.min_cost_flow`. For payload details, see
[problem-type-lp.md](problem-type-lp.md).

## Math Contract

LP has continuous variables only, a single linear objective, and linear
constraints. Result confidence comes from primal feasibility, objective
recomputation, dual feasibility, and a strong-duality check, all within the
declared tolerance; a result without dual values is not accepted.

## Sensitivity

Shadow prices and reduced costs are advisory sensitivity signals when present.
They depend on model scaling, degeneracy, and backend availability. Treat
numerical warnings as reasons to inspect units, coefficient ranges, bounds, and
near-duplicate constraints before retry.

## Special Structure

A linear model with network structure that the dedicated classes do not fit,
such as several commodities sharing arcs, stays LP. Do not escalate to MILP
when the accepted linear structure already gives integer-valued optima through
its network form. Escalate to `2.2.milp` only when the user needs actual
integer, binary, fixed-charge, or either-or decisions.

If a required feature is outside the linear class, follow the out-of-scope
guidance in [problem-type-lp.md](problem-type-lp.md).
