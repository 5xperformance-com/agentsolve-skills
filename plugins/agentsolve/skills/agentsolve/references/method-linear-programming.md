# Method: Linear Programming

Use this when the user describes continuous allocation, blending, production,
transportation, assignment, transshipment, or other linear resource allocation.
For payload details, see [problem-type-lp.md](problem-type-lp.md).

## Math Contract

Stage 0 LP has continuous variables only, a single linear objective, and linear
constraints. Result confidence comes from primal feasibility, objective
recomputation, dual feasibility where populated, and strong-duality checks where
available.

## Sensitivity

Shadow prices and reduced costs are advisory sensitivity signals when present.
They depend on model scaling, degeneracy, and backend availability. Treat
numerical warnings as reasons to inspect units, coefficient ranges, bounds, and
near-duplicate constraints before retry.

## Special Structure

Transportation, assignment, network-flow, and transshipment patterns can often
stay LP. Do not escalate to MILP when the accepted linear structure already
gives integer-valued optima through its network form. Escalate to
`2.2.milp` only when the user needs actual integer, binary, fixed-charge, or
either-or decisions.

If a required feature is outside linear Stage 0, use the typed deferral codes in
[problem-type-lp.md](problem-type-lp.md).
