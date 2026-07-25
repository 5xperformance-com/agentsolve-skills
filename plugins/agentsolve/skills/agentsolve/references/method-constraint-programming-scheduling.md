# Method: Constraint-Programming Scheduling

Stage 0 scheduling uses `4.1.scheduling.rcpsp` for deterministic RCPSP,
MRCPSP, and MSPSP-style project schedules. `4.2.scheduling.jssp` is planned
only. For payload details, see [problem-type-rcpsp.md](problem-type-rcpsp.md).

## Family Scope

Use RCPSP when activities have durations, precedence relations, renewable
resources, calendars, windows, and an optimize or verify-only job intent.
CP-SAT may be an internal admitted backend, but agents must not draft CP-SAT
payloads, option names, or logs.

## Scheduling Semantics

Generalized precedences use `FS`, `SS`, `FF`, and `SF` with `min_lag` and
optional `max_lag`. Calendars are renewable-resource availability over
half-open day ranges. `verify_only` validates a caller-supplied candidate
schedule under the same quote -> job -> poll lifecycle as optimize.

## Deferrals

Use `non_renewable_rcpsp_resource`, `stochastic_durations`, and
`multi_objective_scheduling` as typed deferrals when those semantics are
required. JSSP execution stays planned adjacency, not a launch deferral code.

Proof and bound fields such as `proved_optimal` are diagnostics. The verifier
still recomputes schedule legality.

See [formulation-patterns.md](formulation-patterns.md),
[infeasibility-diagnostics.md](infeasibility-diagnostics.md), and
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
