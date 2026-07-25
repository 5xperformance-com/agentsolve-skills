# Problem Type: RCPSP

Canonical schema versions:

- Input: `4.1.scheduling.rcpsp.input.v2`
- Output: `4.1.scheduling.rcpsp.output.v2`

Use `4.1.scheduling.rcpsp` for deterministic project scheduling with
activities, durations, precedence constraints, renewable resources, calendars,
activity windows, and either `job_intent=optimize` or `job_intent=verify_only`.

## Formulation Recipe

- Activities need stable IDs, duration, and resource use.
- Precedences support `FS`, `SS`, `FF`, and `SF` with `min_lag` and optional
  `max_lag`.
- Resources are renewable and may include calendars with half-open day ranges.
- Activity windows use `release_day` and `due_day`.
- `candidate_schedule` is required for `verify_only` and absent for `optimize`.
- RCPSP activity-count tiers are `S <= 30`, `M <= 200`, and `L > 200`.

Receipt tier is selected at quote time through `constraints.receipt_tier`.
Supported values are `validity_only`, `validity_plus_quality`, and `full`; the
selection is bound to quote, job, and receipt without changing the canonical
problem hash.

Solver availability is discovered through the menu and quote response. Additional
RCPSP execution families may appear as provider-neutral supply, but the payload
remains the canonical schema above and not a backend modelling dialect.

## Deferrals And Adjacency

| Required semantic | Action |
|---|---|
| non-renewable resources | code `non_renewable_rcpsp_resource`, nearest_supported_subset `4.1.scheduling.rcpsp`, roadmap_status `deferred` |
| random durations | code `stochastic_durations`, nearest_supported_subset deterministic RCPSP, roadmap_status `deferred` |
| makespan plus smoothing as separate objectives | code `multi_objective_scheduling`, nearest_supported_subset one accepted linear objective, roadmap_status `deferred` |

`4.2.scheduling.jssp` is planned only. Do not present arbitrary job-shop
execution as a Stage 0 launch class. Rolling rescheduling, arbitrary hierarchy
management, and quadratic smoothing are outside this launch reference.

## Output And Self-Checks

The output cites `4.1.scheduling.rcpsp.output.v2`. Read `schedule[].activity_id`,
`schedule[].start_day`, `schedule[].finish_day`, conditional
`schedule[].mode_id`, top-level `makespan_days`, and objective value.

Before quote creation, check precedence cycles, mode selection, calendar
capacity, activity windows, candidate schedule coverage, and horizon derivation.
The verifier recomputes precedence satisfaction, renewable-resource capacity,
calendar legality, windows, mode legality, and makespan.

## Minimal REST Sketch

```json
{
  "idempotency_key": "quote-rcpsp-001",
  "problem_type": "4.1.scheduling.rcpsp",
  "problem_schema_version": "4.1.scheduling.rcpsp.input.v2",
  "input": {
    "profile": "RCPSP",
    "job_intent": "optimize",
    "activities": [{"id": "A", "duration_days": 2, "resources": {"crew": 1}}],
    "precedences": [],
    "resources": {"crew": {"capacity": 1}},
    "objectives": {"primary": "minimize_makespan"}
  },
  "constraints": {"receipt_tier": "full"}
}
```

## Minimal MCP Sketch

```json
{
  "name": "agentsolve.quotes.create",
  "arguments": {
    "idempotency_key": "quote-rcpsp-001",
    "problem_type": "4.1.scheduling.rcpsp",
    "problem_schema_version": "4.1.scheduling.rcpsp.input.v2"
  }
}
```

Common pitfalls: omitted precedences, calendar gaps, invalid candidate schedules,
oversized horizons, confusing resource leveling with a second objective, and
using `time_budget_ms` as a modelling deadline.

For scheduling-method and result-confidence guidance, see
[method-constraint-programming-scheduling.md](method-constraint-programming-scheduling.md),
[infeasibility-diagnostics.md](infeasibility-diagnostics.md), and
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
