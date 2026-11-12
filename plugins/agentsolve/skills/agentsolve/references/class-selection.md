# Class Selection

Choose the most specific class whose whole boundary fits the real decision,
then open only that class's reference (`problem-type-*.md`, linked from the
first page). It holds that class's fields, customer phrasings and refused
variants. Use LP or MILP only for a naturally linear model, not to get around
another class's boundary. If a needed semantic is refused, say so before
creating a quote; never drop or approximate it.

| Class | Select when | Not when |
|---|---|---|
| `1.1.tsp` | one directed Hamiltonian tour visits every node | capacity, multiple tours, optional nodes, prizes, or visit times matter |
| `1.2.vrp.cvrp` | capacitated routing from one or more depots, optionally with per-vehicle fixed costs, per-customer vehicle eligibility, paired pickup and delivery, and hard or priced time windows over static travel | split delivery, time-dependent travel, or rich vehicle types matter |
| `2.1.lp` | all decisions are continuous and every expression is linear | integrality, nonlinear, stochastic, rolling re-solve, or native multi-objective semantics matter |
| `2.2.milp` | at least one linear-model decision is integer or binary | nonlinear, stochastic, rolling re-solve, or native multi-objective semantics matter |
| `2.3.qp` | all decisions are continuous, every constraint is linear, and the objective is a convex quadratic such as a variance, a least-squares fit, or a quadratic penalty | integer decisions, a non-convex objective, quadratic constraints, conic or robust uncertainty sets, or native multi-objective semantics matter |
| `3.1.newsvendor` | independent single-period SKU quantities use explicit discrete demand scenarios | periods, coupled capacity, correlated demand, risk constraints, ambiguity sets, or rolling policy matter |
| `4.1.scheduling.rcpsp` | fixed or submitted modes schedule project activities over renewable resources, non-renewable budgets, and precedences | stochastic durations, smoothing, or another objective matter |
| `4.2.scheduling.jssp` | each job has a fixed ordered chain of operations, each on a fixed machine or one chosen from declared options, minimizing makespan or total (optionally weighted) tardiness against release and due days | setup sequence, preemption, blocking, or transport matter |
| `4.3.scheduling.rostering` | dated staff-slot assignments meet exact-match coverage and hard work rules at minimum integer penalty | contracts, bidding, recurring patterns, sites, on-call states, rolling repair, or ambiguous multi-skill slot roles matter |
| `5.1.assignment` | unit-demand tasks use sparse allowed agent-task pairs and integer weights | multi-unit consumption, preference stability, or pairwise interactions matter |
| `9.1.knapsack` | indivisible items maximize value under one capacity, each item taken up to its quantity bound | several capacities or containers, fractions, dependencies, uncertainty, or several objectives matter |
| `9.2.set_cover` | a minimum-total-cost subset of sets must cover every element at least its demand times, or leave it short at a declared per-unit penalty | capacities, interactions, uncertainty, or several objectives matter |
| `9.3.bin_packing` | indivisible one-dimensional items use the lowest-cost bins drawn from priced bin types, optionally with conflict separation | dimensions, eligibility, splitting, or several objectives matter |
| `6.1.min_cost_flow` | one commodity moves through a directed network from supplies to demands at least cost, with integer quantities, arc capacities and optional minimum shipments | several commodities share arcs, costs are not linear per unit, a route has a fixed charge, node capacities are not modelled by splitting, or supply and demand do not balance |

## Refused For Every Class

A typed deferral is a refusal with a code. Give the caller the code and the
reason instead of a quote.

| Customer phrasing | Decision | Notes |
|---|---|---|
| "optimize profit and emissions and return a Pareto frontier" | typed deferral `native_multi_objective_optimization` | Say so before quoting. This label is not a service code: rejection is class-specific (`knapsack_multiobjective`, for example) or `INVALID_PAYLOAD`. A caller-approved scalar objective is a different decision. |
| "chance constrained capacity planning" | typed deferral `chance_constrained_optimization` | Expected-value modelling is not a chance constraint. |
| "send this OR-Tools or HiGHS native payload" | typed deferral `provider_native_payload_required` | Submit the canonical AgentSolve schema. The service has no such code: a native payload is refused as `INVALID_PAYLOAD`. |
