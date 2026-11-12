# Examples

This directory contains one self-contained quote -> job -> poll example per
launch class. Each script defaults to a deterministic dry run and accepts
`--base-url` or `AGENTSOLVE_BASE_URL` to run against the API. Dry-run
canonical hashes are pinned to the published seeded payload hashes, so the
examples stand alone.

Live runs select the quote's default candidate explicitly via
`selected_algorithms`, falling back to `auto_route: true` only when the
quote names no default candidate. Authentication comes from the
environment: `AGENTSOLVE_API_TOKEN` is sent as a bearer token
(`AGENTSOLVE_DEV_SCOPES` additionally supports local development
deployments). The live mode pays with trial credit
(`AGENTSOLVE_TRIAL_CREDIT_CODE`), which needs a claimed account, or runs a
quote that needs no payment. Without either it stops before creating a job
and says which rails the quote offers. A newly registered agent pays by
x402: use `--dry-run` to see the request and result shapes, and submit the
same problem with `tools/submit.py`, which hands the payment to your wallet.
The examples never rely on an implicit routing default.
