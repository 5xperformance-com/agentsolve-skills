# Problem Type: Job-Shop Scheduling

Canonical schema versions:

- Input: `4.2.scheduling.jssp.input.v3`
- Output: `4.2.scheduling.jssp.output.v4`

Use `4.2.scheduling.jssp` when each job is a fixed, ordered chain of
operations, every operation runs on one named machine for an integer
duration, machines process one operation at a time, and the goal is the
shortest makespan — or, with per-job release and due dates, the smallest
total tardiness.

## Formulation Recipe

- `machines`: unique machine identifiers.
- `jobs`: unique job identifiers, each with an ordered `operations` list.
- Each operation names its `machine_id` and integer `duration_days`.
- An operation that could run elsewhere adds `machine_options`, one entry per
  alternative machine with that machine's own `duration_days`. The declared
  `machine_id` is the default choice and is part of the option set, so a
  machine appears once with one duration. Omit the field for a fixed machine.
- **Operation order is the problem.** The platform sorts jobs and machines
  into canonical order but never reorders operations; reordering them is a
  different instance and produces a different canonical hash.
- Objective: `minimize_makespan` (the default) or `minimize_total_tardiness`.
- Any job may declare an integer `release_day` (default 0) under either
  objective. No operation of a job starts before its release day.
- Under `minimize_total_tardiness` every job declares an integer `due_day`
  and may declare an integer `weight` (default 1). The objective is the exact
  integer sum over jobs of `weight * max(0, completion - due_day)`.
- Operation-count tiers are `S <= 100`, `M <= 450`, and
  `451 <= L <= 6,250,000`. The schema caps jobs and machines at 2,500 and
  operations per job at 2,500. Inspect machine-option count and objective in
  the descriptor when evaluating measured performance.

## Deferrals

| Required semantic | Action |
|---|---|
| eligible machines without a duration for each | typed deferral code `jssp_flexible_machine_choice`; use `machine_options`, which names each machine's own duration |
| changeover times that depend on processing order | typed deferral code `jssp_sequence_dependent_setup` |
| due dates under the makespan objective | typed deferral code `jssp_release_and_due_dates`; declare `minimize_total_tardiness` to use them |
| per-job weights under the makespan objective | typed deferral code `jssp_weighted_tardiness`; makespan counts no job weight |
| interrupting an operation once started | typed deferral code `jssp_preemption` |
| no-wait or blocking transfers between operations | typed deferral code `jssp_no_wait_or_blocking` |
| travel time between machines | typed deferral code `jssp_transport_moves` |

## Result Interpretation

The output cites `4.2.scheduling.jssp.output.v4` with the full `schedule`
(one row per operation, with its machine, start day, and finish day), the
`makespan_days`, and `solver_status`. Total-tardiness results additionally
carry `total_tardiness_days`, the plain sum over jobs; when any job declares a
`weight`, `objective_value` is the weighted sum and `total_weighted_tardiness_days`
repeats it. Makespan results leave both tardiness fields absent or null.

The verifier independently checks machine exclusivity, the per-job precedence
chain, machine assignment, processing durations, and release-date observance,
then recomputes the declared objective — makespan, or total tardiness against
the due dates. A raw `proved_optimal` field is diagnostic. The receipt carries
`solver_proved` only after an admitted adapter supplies an explicit terminal
proof signal. Job shop carries no independent optimality certificate.

Published optima for named benchmark instances are regression comparisons,
never certificates.

## Time budgets

Job shop is NP-hard and the launch resource envelope is not yet qualified.
Use discovered limits and treat a time limit as a budget, never as an
optimality guarantee. A valid incumbent may settle as feasible without a
proof; a result that the verifier cannot validate must refund.

## Job intents

- `optimize` — schedule and report honestly.
- `verify_only` — supply `candidate_schedule` (a start day per operation,
  covering every operation exactly once) and get validity plus the exact
  recomputed objective.

## Minimal REST Sketch

```json
{
  "idempotency_key": "quote-jssp-001",
  "problem_type": "4.2.scheduling.jssp",
  "problem_schema_version": "4.2.scheduling.jssp.input.v3",
  "input": {
    "machines": ["cutting", "welding"],
    "jobs": [
      {
        "id": "frame",
        "operations": [
          {"machine_id": "cutting", "duration_days": 2},
          {"machine_id": "welding", "duration_days": 3}
        ]
      },
      {
        "id": "panel",
        "operations": [
          {"machine_id": "welding", "duration_days": 2},
          {"machine_id": "cutting", "duration_days": 1}
        ]
      }
    ],
    "objectives": {"primary": "minimize_makespan"}
  }
}
```

For the total-tardiness variant, declare the objective and per-job dates:

```json
{
  "objectives": {"primary": "minimize_total_tardiness"},
  "jobs": [
    {
      "id": "frame",
      "release_day": 1,
      "due_day": 6,
      "operations": [
        {"machine_id": "cutting", "duration_days": 2},
        {"machine_id": "welding", "duration_days": 3}
      ]
    }
  ]
}
```
