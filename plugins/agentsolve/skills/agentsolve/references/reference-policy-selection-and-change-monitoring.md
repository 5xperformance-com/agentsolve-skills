# Policy Selection And Change Monitoring

Use policy fields to express caller constraints, not solver tuning. The
`policy` object is required on every quote request; within it,
`max_price_usdc` is mandatory and everything else is optional. There are
no service tiers: every job runs on the one production path, and a stray
`service_tier` key is rejected as an unknown field.

## Policy Fields

- `max_price_usdc` (required): hard price ceiling.
- `max_latency_seconds`: caller latency tolerance.
- `quality_floor`: minimum acceptable quality estimate.
- `minimum_evidence_state`: `declared_only` (default), `qualification_only`,
  or `production_observed` — the evidence bar candidates must meet.
- `exploration_mode`: exploration posture; default `none`.
- `failover_mode`: failover posture; default `strict`.
- `allowed_regions`: permitted serving regions.
- `pin`: pin a previously quoted selection.
- `allowed_solver_families`: optional family allow-list.
- `excluded_solver_families`: optional family deny-list.

Quote responses may include dominance reasons, policy eliminations, typed quote
rejections, `degraded_mode`, and warning blocks. Explain these directly instead
of silently loosening the caller policy.

## Change Monitoring

Use `GET /v1/transparency/changes` and schema discovery surfaces to monitor
contract, policy, schema-support-window, and market-readiness changes. Do not
scrape planning prose as the operational source of truth.

See [reference-degraded-and-non-guarantees.md](reference-degraded-and-non-guarantees.md).
