# Problem Type: RCPSP

Contents: Customer Phrasing · Formulation Recipe · Deferrals And Adjacency · Output And Self-Checks · Minimal REST Sketch

Canonical schema versions:

- Input: `4.1.scheduling.rcpsp.input.v3`
- Output: `4.1.scheduling.rcpsp.output.v3`

Use `4.1.scheduling.rcpsp` for deterministic project scheduling with
activities, durations, precedence constraints, renewable resources, calendars,
non-renewable resource budgets, and activity windows. Send
`job_intent=optimize`. Checking an existing schedule is not available yet: a
quote with `job_intent=verify_only` is refused with `NO_ELIGIBLE_SOLVER`.

## Customer Phrasing

| Customer phrasing | Decision | Notes |
|---|---|---|
| "schedule activities with crews and precedence" | `4.1.scheduling.rcpsp` | Renewable resources and submitted precedences. |
| "materials or cash have one total budget for the project" | `4.1.scheduling.rcpsp` | Declare `non_renewable_resources` budgets and per-mode consumption. |
| "verify this submitted project schedule" | not available | The schema takes `job_intent=verify_only`, but no admitted solver performs the check: the quote is refused with `NO_ELIGIBLE_SOLVER`. |
| "durations are random and we need a robust schedule" | typed deferral `stochastic_durations` | Durations are deterministic integers. |
| "optimize makespan and resource smoothing together" | typed deferral `multi_objective_scheduling` | The class objective is makespan only. |

## Formulation Recipe

- Activities need stable IDs, duration, and resource use.
- Precedences support `FS`, `SS`, `FF`, and `SF` with `min_lag` and optional
  `max_lag`.
- Resources are renewable and may include calendars with half-open day ranges.
- `non_renewable_resources` declares consumables, each with one integer
  `budget` for the whole project, under IDs disjoint from renewable
  resources. A mode (or single-mode activity) declares its integer
  consumption per consumable, spent once if that mode runs; the selected
  modes' summed consumption must fit each budget.
- Activity windows use `release_day` and `due_day`.
- Omit `candidate_schedule`: it is refused when `job_intent=optimize`.
- RCPSP activity-count tiers are `S <= 20`, `M <= 60`, and
  `61 <= L <= 2,500`; precedences are capped at 10,000. The quote descriptor
  also reports modes, resources, projects, generalized lags, calendars, and
  the derived horizon.

Receipt tiers are not offered. Omit `constraints.receipt_tier`; an explicit
non-null tier request is rejected. The compatibility field remains nullable in
responses, and every settled job receives the full standard receipt.

Solver availability is discovered through the menu and quote response. Additional
RCPSP engines may appear, but the payload remains the canonical schema above
and not a backend modelling dialect.

## Deferrals And Adjacency

| Required semantic | Action |
|---|---|
| random durations | code `stochastic_durations`, nearest_supported_subset deterministic RCPSP, roadmap_status `deferred` |
| makespan plus smoothing as separate objectives | code `multi_objective_scheduling`, nearest_supported_subset minimum makespan only, roadmap_status `deferred` |

`4.2.scheduling.jssp` has its own launch-scoped canonical contract. Do not
substitute it for rolling rescheduling, arbitrary hierarchy management, or
quadratic smoothing.

## Output And Self-Checks

The output cites `4.1.scheduling.rcpsp.output.v3`. Read `schedule[].activity_id`,
`schedule[].start_day`, `schedule[].finish_day`, conditional
`schedule[].mode_id`, top-level `makespan_days`, and objective value.

Before quote creation, check precedence cycles, mode selection, calendar
capacity, non-renewable budgets against minimum consumption, and activity
windows. The input has no horizon field: the quote descriptor derives the
horizon, and a `horizon` key is refused. The verifier recomputes precedence
satisfaction, renewable-resource capacity, calendar legality, non-renewable
budget consumption, windows, mode legality, and makespan.

## Minimal REST Sketch

```json
{
  "idempotency_key": "quote-rcpsp-001",
  "problem_type": "4.1.scheduling.rcpsp",
  "problem_schema_version": "4.1.scheduling.rcpsp.input.v3",
  "input": {
    "profile": "RCPSP",
    "job_intent": "optimize",
    "activities": [{"id": "A", "duration_days": 2, "resources": {"crew": 1}}],
    "precedences": [],
    "resources": {"crew": {"capacity": 1}},
    "objectives": {"primary": "minimize_makespan"}
  },
  "policy": {"max_price_usdc": "0.50"}
}
```

Over MCP, pass the same object as the `arguments` of
`agentsolve.quotes.create`.

Common pitfalls: omitted precedences, calendar gaps, budgets declared without
any mode consumption, requesting a withdrawn receipt tier, confusing resource
leveling with a second objective, and using `time_budget_ms` as a modelling
deadline.

For scheduling-method and result-confidence guidance, see
[method-constraint-programming-scheduling.md](method-constraint-programming-scheduling.md),
[infeasibility-diagnostics.md](infeasibility-diagnostics.md), and
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
