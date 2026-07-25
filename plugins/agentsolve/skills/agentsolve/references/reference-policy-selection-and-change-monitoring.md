# Policy Selection And Change Monitoring

Use policy fields to express caller constraints, not solver tuning.

## Policy Fields

- `service_tier`: latency/quality/economics tier requested by the caller.
- `max_price_usdc`: hard price ceiling.
- `max_latency_seconds`: caller latency tolerance.
- `quality_floor`: minimum acceptable quality estimate.
- `allowed_regions`: permitted serving regions.
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
