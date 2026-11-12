# Method: Constraint-Programming Scheduling

Scheduling uses `4.1.scheduling.rcpsp` for deterministic RCPSP, MRCPSP, and
MSPSP-style project schedules, `4.2.scheduling.jssp` for fixed-route job
shops, and `4.3.scheduling.rostering` for staff rosters. For payload details,
see [problem-type-rcpsp.md](problem-type-rcpsp.md),
[problem-type-jssp.md](problem-type-jssp.md), and
[problem-type-rostering.md](problem-type-rostering.md).

## Family Scope

Use RCPSP when activities have durations, precedence relations, renewable
resources, calendars, non-renewable budgets, and windows. Checking an existing
project schedule is not available yet.

CP-SAT may be an internal admitted backend, but agents must not draft CP-SAT
payloads, option names, or logs.

## Scheduling Semantics

Generalized precedences use `FS`, `SS`, `FF`, and `SF` with `min_lag` and
optional `max_lag`. Calendars are renewable-resource availability over
half-open day ranges. `non_renewable_resources` declares whole-project
consumable budgets spent once per selected mode.

## Deferrals

Use `stochastic_durations` and `multi_objective_scheduling` as typed
deferrals when those semantics are required. JSSP has its own launch-scoped
canonical contract; it is not an RCPSP deferral code.

Proof and bound fields such as `proved_optimal` are diagnostics. The verifier
still recomputes schedule legality.

See [formulation-patterns.md](formulation-patterns.md),
[infeasibility-diagnostics.md](infeasibility-diagnostics.md), and
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
