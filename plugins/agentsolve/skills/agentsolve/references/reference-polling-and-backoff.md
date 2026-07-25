# Polling And Backoff

The correctness surface is job polling. After quote acceptance and job creation,
poll `GET /v1/jobs/{job_id}` or `agentsolve.jobs.get` until `terminal=true`.

## Polling Rules

- Respect `recommended_poll_after_ms`; do not tight-loop.
- Treat disconnects as retryable reads, not evidence of job failure.
- Preserve idempotency keys when retrying creation calls.
- Terminal reads have `recommended_poll_after_ms=0`.
- Non-terminal reads may include progress fields, but progress delivery is not
  the source of correctness.

## Terminal Handling

- `SETTLED`: read output and receipt together.
- `REFUNDED`: do not retry blindly; inspect error and refund context.
- `DISPUTED`: use dispute or transparency surfaces for follow-up.
- `SUPERSEDED`: use the replacement or repaired receipt path when present.

For result confidence, see
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
