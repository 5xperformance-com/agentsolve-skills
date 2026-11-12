# Infeasibility Diagnostics

Use this reference when a quote, job, result, or receipt reports an infeasible,
unbounded, time-limited, or warning-bearing outcome.

## Label

One label is in use: `semantic_diagnostic`, set when the verifier rejects a
result. It is the value of `infeasibility_diagnostic.label`, and
`infeasibility_diagnostic.summary` carries the verifier's reason. A result the
verifier accepts carries no diagnostic.

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
