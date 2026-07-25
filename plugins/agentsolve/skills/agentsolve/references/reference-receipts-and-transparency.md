# Receipts And Transparency

Stage 0 receipts use `receipt.v3` for new engine-era diagnostics. `receipt.v2`
is immutable legacy and should be mentioned only for historical compatibility.

## Receipt Fields

Read `solver_status`, `optimality_gap`, `best_bound`,
tenant-scoped `reduced_costs`, `solver_hints_hash`, `warnings[]`,
`infeasibility_diagnostic`, normalized class metrics, `optimality_certified`,
and `proved_optimal` where applicable.

Engine-backed LP/MILP jobs may populate solver status, gap, bound, reduced
costs, and capability fingerprint fields. Domain adapters such as TSP, CVRP,
RCPSP, and newsvendor may leave some engine-backed fields null while still
settling with verifier evidence.

`proved_optimal` and `optimality_certified` are not interchangeable.
`receipt.v3` exposes one `optimality_gap`, not separate absolute and relative
gap fields. To interpret hint choices, consult the originating quote's
`solver_hints` and compare `solver_hints_hash`.

## Visibility

Tenant-scoped receipts expose all commercial fields. Public transparency
records redact provider/platform split amounts and tenant-only reduced costs.
Use `GET /v1/transparency/changes` for public changes and
`GET /v1/transparency/jobs/{job_id}` for targeted job transparency.

See [reference-verification-and-certificates.md](reference-verification-and-certificates.md).
