# Method: Stochastic Newsvendor

Use this when the math is a single-period order quantity under explicit
discrete demand. For payload details, see
[problem-type-newsvendor.md](problem-type-newsvendor.md).

## Math Contract

The decision is one order quantity for one period. Demand must be represented by
explicit outcomes and probabilities: each item lists its demand scenarios, and
one item's probabilities must sum to 1. The verifier recomputes expected cost
or expected profit over those outcomes. Inside its work cap it also enumerates
the order grid exactly and certifies a result that matches the optimum.

## Scenario Quality

Ask whether observations are true demand or censored sales. Small samples,
promotion periods, stockouts, and correlated multi-SKU behavior can make the
scenario set misleading. SAA-style scenario reasoning is acceptable only when
the scenarios are explicitly supplied and accepted by the caller.

## Risk Boundary

Newsvendor optimizes expected cost or expected profit. The API answers needs
beyond that with typed deferral codes:

- a required risk constraint: deferral code `chance_constrained_optimization`
- an ambiguity set: deferral code `distributionally_robust_inventory`
- several ordering periods: deferral code `multi_period_inventory`
- a rolling reorder policy: deferral code `rolling_inventory_policy`
