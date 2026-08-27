# Infeasibility Diagnostics

Use this reference when a quote, job, result, or receipt reports an infeasible,
unbounded, time-limited, or warning-bearing outcome.

## Closed Labels

`infeasibility_diagnostic.label` uses these closed agent-facing labels:

- `formal_iis`: a formal irreducible infeasible subsystem style explanation.
- `conflict_candidate`: a bounded conflict explanation when a formal proof is
  not available.
- `semantic_diagnostic`: a domain or verifier explanation such as missing
  capacity, impossible activity windows, or invalid candidate schedule.
- `routing_infeasibility_certificate`: routing-specific capacity, timing,
  coverage, or route-duration impossibility.

## Handling

- Infeasible: ask which constraints, windows, demands, or capacities may change.
- Unbounded: ask for missing upper/lower bounds or objective limits.
- Time-limited with incumbent: report incumbent quality, `best_bound`, and
  `optimality_gap`; do not call it optimal.
- Numerical warning: inspect units, coefficient scaling, and weak big-M values.

Proof flags, gaps, and bounds are solver diagnostics rather than verifier
certificates. Use
[reference-verification-and-certificates.md](reference-verification-and-certificates.md)
for result-confidence guidance.
