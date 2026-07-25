# Examples

This directory contains one self-contained quote -> job -> poll example per
Stage 0 launch class. Each script defaults to deterministic dry-run output for
CI and accepts `--base-url` or `AGENTSOLVE_BASE_URL` for local integration use.
Dry-run canonical hashes are pinned to the published seeded payload hashes so
the examples remain standalone for provider-neutral consumers. Repository tests
recompute those hashes through the local AgentSolve canonical registry.

Live runs submit `auto_route: true` explicitly. Set
`AGENTSOLVE_TRIAL_CREDIT_CODE` for trial-credit execution, use a faucet-funded
quote that returns `payment_requirement.requires_payment=false`, or adapt the
payment object from the quote's available `payment_requirement` option. The
examples never rely on an implicit routing default.
