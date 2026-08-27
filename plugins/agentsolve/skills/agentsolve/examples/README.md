# Examples

This directory contains one self-contained quote -> job -> poll example per
Stage 0 launch class. Each script defaults to deterministic dry-run output for
CI and accepts `--base-url` or `AGENTSOLVE_BASE_URL` for local integration use.
Dry-run canonical hashes are pinned to the published seeded payload hashes so
the examples remain standalone for provider-neutral consumers. Repository tests
recompute those hashes through the local AgentSolve canonical registry.

Live runs select the quote's default candidate explicitly via
`selected_algorithms`, falling back to `auto_route: true` only when the
quote names no default candidate. Authentication comes from the
environment: `AGENTSOLVE_API_TOKEN` is sent as a bearer token
(`AGENTSOLVE_DEV_SCOPES` additionally supports local development
deployments). For payment, set `AGENTSOLVE_TRIAL_CREDIT_CODE` for
trial-credit execution, use a faucet-funded quote that returns
`payment_requirement.requires_payment=false`, or let the example create a
quote-bound Stripe PaymentIntent through the documented preflight. The
examples never rely on an implicit routing default.
