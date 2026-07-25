# Method: Stochastic Newsvendor

Use this when the math is a single-period order quantity under explicit
discrete demand. For payload details, see
[problem-type-newsvendor.md](problem-type-newsvendor.md).

## Math Contract

The decision is one order quantity for one period. Demand must be represented by
explicit outcomes and probabilities or scenario weights. The verifier recomputes
expected cost or expected profit over those outcomes and may use closed-form or
grid evidence for the launch class.

## Scenario Quality

Ask whether observations are true demand or censored sales. Small samples,
promotion periods, stockouts, and correlated multi-SKU behavior can make the
scenario set misleading. SAA-style scenario reasoning is acceptable only when
the scenarios are explicitly supplied and accepted by the caller.

## Risk Boundary

Stage 0 newsvendor optimizes expected cost or expected profit. Required risk
constraints, distributionally robust inventory, or multi-period rollout should
be routed to `chance_constrained_optimization` or `multi_period_inventory`
deferral guidance as appropriate.
