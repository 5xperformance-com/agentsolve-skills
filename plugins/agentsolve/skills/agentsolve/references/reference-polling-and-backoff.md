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

## Portfolio Cohorts

`terminal` is the aggregate signal for a portfolio: the polled job's own
`status` can be `SETTLED` while `terminal` stays `false` because sibling
members are still running — never stop polling on `status` alone.
`cohort_members` reports each member's status, terminality, and — as soon
as that member finishes — its own attested `routing_receipt` plus, when a
result exists, an `output_url` that is readable immediately, before the
rest of the cohort completes. Every settled member carries its own
verifier-attested result: obtain each one separately, attribute it to the
algorithm on its receipt, and keep the best by the problem's objective
sense (a refunded member, including the polled head, contributes nothing).
Cohort agreement is an algorithmic cross-check — distinct algorithms on
one platform; the receipt's `degraded_mode` and
`independent_family_count_bucket` fields state exactly what "independent"
means for the job, so reconcile any independence claim with them. Portfolio cancellation is all-or-none and
closes once any member starts; to bound waiting, stop polling at your own
threshold of settled members and let the rest run.

For result confidence, see
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
