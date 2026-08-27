# Receipts And Transparency

Current receipts use `receipt.v5`. Earlier versions remain immutable and
readable for historical compatibility.

## Receipt Fields

Read `solver_status`, `optimality_gap`, `best_bound`,
tenant-scoped `reduced_costs`, `solver_hints_hash`, `warnings[]`,
`infeasibility_diagnostic`, normalized class metrics, `optimality_certified`,
and `proved_optimal` where applicable. Read `established_guarantee` for the
platform verifier's conclusion and `attestation.claims` for its source and
named proposition. `instance_descriptor_hash` binds the quote-time feature
projection; `validity_envelope_id` and `proof_envelope_id` identify the
verifier contracts exercised.

Engine-backed LP/MILP jobs may populate solver status, gap, bound, reduced
costs, and capability fingerprint fields. Domain adapters such as TSP, CVRP,
RCPSP, and newsvendor may leave some engine-backed fields null while still
settling with verifier evidence.

`proved_optimal` and `optimality_certified` are backward-compatible
solver diagnostics guarded by an explicit terminal proof signal. They are not
verifier certificates, and neither a zero gap nor objective equality creates a
claim.
`receipt.v5` exposes one `optimality_gap`, not separate absolute and relative
gap fields. To interpret hint choices, consult the originating quote's
`solver_hints` and compare `solver_hints_hash`.

## Visibility

Tenant-scoped receipts expose all commercial fields. Public transparency
records redact provider/platform split amounts and tenant-only reduced costs.
Use `GET /v1/transparency/changes` for public changes and
`GET /v1/transparency/jobs/{job_id}` for targeted job transparency.

See [reference-verification-and-certificates.md](reference-verification-and-certificates.md).
