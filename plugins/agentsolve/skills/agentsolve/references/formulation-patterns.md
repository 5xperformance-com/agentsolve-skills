# Formulation Patterns

Use these patterns only when they emit an ordinary supported Stage 0 LP, MILP,
CVRP, or RCPSP payload. If a required semantic does not fit, use typed deferral
before quote creation.

## LP And MILP Patterns

- choose-K: binary variables with `sum(x) = K`.
- set covering: `sum(covering choices) >= 1`.
- set packing: `sum(conflicting choices) <= 1`.
- set partitioning: `sum(assigned choices) = 1`.
- if-then: binary trigger with tight big-M derived from real bounds.
- either-or: binary selector over two bounded linear alternatives.
- fixed charge: binary open variable plus bounded flow or assignment variable.
- piecewise-linear convex cost: linear segment variables and accepted breakpoints.
- absolute value in objective: positive and negative deviation variables.
- min-max or max-min: auxiliary bound variable and linear linking constraints.
- goal programming: goal-programming single-objective LP/MILP reformulation.
- symmetry breaking: deterministic ordering constraints that do not remove
  valid business solutions.
- stay close to a known plan: when the reference plan is a constant, penalising
  each change is a cost reweighting, not a new variable. Subtract the penalty
  from the weight of every choice the reference already makes and add it to
  every choice it does not; the optimum is the same one an explicit difference
  term would give. Classes that price churn as a declared field, such as
  rostering, take the field instead.

## Routing And Scheduling Patterns

- route-visit constraints: each required customer appears once unless the class
  explicitly says otherwise.
- cumulative capacity: track load or resource use against vehicle or renewable
  resource capacity.
- hard windows: propagate arrival, service start, and service completion using
  a single time base.
- RCPSP horizon: derive a finite horizon from durations, calendars, and windows
  rather than using a casual oversized value.

Weighted-sum single-objective LP/MILP reformulation,
lexicographic staged single-objective LP/MILP solve, and
threshold-plus-objective single-objective LP/MILP formulation are
allowed only when each solve remains an ordinary single-objective Stage 0 job.
