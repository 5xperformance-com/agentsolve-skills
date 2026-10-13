# Errors And Retries

All agent-facing failures use the stable V5 error envelope with `code`,
`message`, `retryable`, `idempotency_relevant`, and redacted `details`.

## Error Code Inventory

| Code | Typical handling |
|---|---|
| `PROBLEM_NOT_SUPPORTED` | Reclassify or defer before quote creation. |
| `NO_ELIGIBLE_SOLVER` | Adjust policy or try later if supply changes. |
| `INVALID_PAYLOAD` | Correct canonical input; do not retry unchanged. |
| `INPUT_UPLOAD_UNAVAILABLE` | Upload handles are disabled on this deployment; send the input inline. |
| `INTERNAL_ERROR` | Retry only when `retryable=true`; preserve idempotency key. |
| `QUOTE_EXPIRED` | Create a fresh quote. |
| `PAYMENT_REQUIRED` | A job request carries no payment for a quote that needs one; read `details.extra.payment_requirement` for the available funding options and resubmit the job with one of them. |
| `PAYMENT_AUTH_FAILED` | Correct the funding path or ask the caller to reauthorize; when `details.extra.retry_after_seconds` is present (velocity windows span hours), wait that long rather than retrying on minutes-scale backoff. `settlement_outcome: settled` with `remedy: x402_credit_fallback` means the x402 payment settled and was credited to the account: resubmit the same job request (same quote, same idempotency key) paying from account credit with `details.extra.remedy_payment_authority_id` (also listed by `GET /v1/payments/authorities`), never by replaying the same payment. A fresh x402 signature needs a fresh quote, which an autonomous account can take only after this one expires. |
| `JOB_NOT_FOUND` | Check account scope and the resource id. |
| `IDEMPOTENCY_CONFLICT` | Do not reuse the key for different material inputs. |
| `QUOTE_HINTS_MISMATCH` | Pass the quote's `effective_solver_hints` verbatim on the job, or create a new quote. |
| `INVALID_JOB_STATE` | Follow the lifecycle; do not force the transition. |
| `OUTPUT_NOT_AVAILABLE` | The job ended without a deliverable result (only a `SETTLED` job has one); read the job's `terminal_diagnostic` for why and recover from there. |
| `OUTPUT_EXPIRED` | The output copy aged out of retention; re-submit the job if you still need the result. |
| `ROUTING_MODE_NOT_SPECIFIED` | Include exactly one routing mode on job creation. |
| `ROUTING_MODE_AMBIGUOUS` | Send only one of `auto_route` / `selected_algorithms`. |
| `SELECTED_ALGORITHM_NOT_IN_QUOTE` | Select only solver admission ids the quote offered. |
| `COHORT_SIZE_EXCEEDED` | Portfolio jobs take at most 10 solver admission ids. |
| `COHORT_HEAD_REQUIRED` | Cancel a portfolio only through its cohort head job; the response names the head job's ID. |
| `UNSUPPORTED_FAILOVER_MODE` | Set `policy.failover_mode` to `strict`; Stage 0 does not implement any other failover posture. |
| `MODE_3_NO_ELIGIBLE_CANDIDATE` | Relax the policy or select a solver explicitly. |
| `CONCURRENT_QUOTE_CONSUMPTION` | Poll or retry with the same idempotency key. |
| `AUTHENTICATION_REQUIRED` | Refresh credentials. |
| `IDENTITY_BOOTSTRAP_CONFLICT` | The identity was already bootstrapped; reuse the stored credential. |
| `ORIGIN_NOT_ALLOWED` | Use an allowed MCP or REST origin. |
| `RATE_LIMITED` | Back off according to server guidance. `tools/submit.py` retries these itself with bounded backoff. |

Typed quote rejections should be interpreted before retry. If the rejection is
a typed deferral, return the deferral code, nearest supported subset, and
roadmap status rather than approximating the user's requirement.

## Job Status → Diagnostic → Recovery

A terminal job or cohort member carries its own explanation:

| Status | Where to look | Recovery |
|---|---|---|
| `SETTLED` | `output_url`, `routing_receipt` | None needed — the receipt is the deliverable. |
| `REFUNDED` | `terminal_diagnostic` (`code`, `fault_class`, `refund_disposition`) | Platform fault (`fault_class: "platform"`): re-submit; you were not charged. Input fault: fix the named field first. |
| `DISPUTED` / `SUPERSEDED` | `terminal_diagnostic` | Read the diagnostic; these are not retry targets. |

### `terminal_diagnostic.failure_code` on a refunded job

`retryable` answers "is resubmitting the same request worth it", not "will the
platform retry". A solver-owned code is not retryable: the same request reaches
the same solver and the same outcome. You are never charged for a refunded job.

| Code | Meaning | Recovery |
|---|---|---|
| `NON_ZERO_EXIT` | The solver process failed on this input. | Not retryable as-is: select another admitted solver or reduce the instance. |
| `TIME_LIMIT_EXCEEDED` | The solver was stopped at its wall budget without a result. | Not retryable as-is: raise `time_limit_seconds` where the class applies it, or select another solver. |
| `MEMORY_LIMIT_EXCEEDED` | The solver exceeded its memory envelope. | Not retryable as-is: reduce the instance or select another solver. |
| `OUTPUT_CONTRACT_VIOLATION` | The solver ended without a result the class accepts: no solution, or unreadable or schema-invalid output. | Not retryable as-is: select another solver. |
| `SECURITY_POLICY_VIOLATION` | The solver violated the runtime's isolation policy. | Not retryable; report it. |
| `VERIFIER_REJECTED` | The solver returned a result the verifier refused: invalid, or a proof it could not confirm. | Not retryable as-is: select another solver. |
| `CANCELED_BY_CALLER` | You cancelled before execution. | Nothing to do. |
| `MEMBER_FAILED_VERIFICATION`, `MEMBER_EXECUTION_INCOMPLETE` | One portfolio member was refunded; the others stand. | Read the cohort agreement; re-submit only the work you still need. |
| `UNEXPECTED_WORKER_ERROR`, `HOST_AGENT_ERROR`, `VM_BOOT_FAILURE`, `IMAGE_DIGEST_MISMATCH`, `PLATFORM_DISPATCH_TIMEOUT`, `PLATFORM_CLAIM_LOST`, `PLATFORM_DRAIN_CANCELLED`, `RUNTIME_UNAVAILABLE` | A platform-side fault; the platform already retried where a retry could help. | `retryable: true`: re-submit with a fresh idempotency key. |
| `EXECUTION_FAILED`, `SETTLEMENT_FAILED`, `TERMINATED` | A platform-side refund without a more specific record. | Treat as a platform fault: re-submit. |

## Observed Rate-Limit and Replay Shapes

- **HTTP 429 `RATE_LIMITED`** on job creation: read
  `details.extra.authorization_consumed`. When it is absent or `false`
  (Stripe, account credit, trial credit; `retryable: true`) wait, honouring
  `Retry-After` when present, and retry the identical request with the same
  idempotency key; `tools/submit.py` does this automatically (bounded
  attempts with jitter). When it is `true` (`retryable: false`: an x402
  payment that settled before the refusal) the settled amount is credited to
  the account: wait, honouring `Retry-After` when present, then resubmit the
  same job request (same quote, same idempotency key) paying from account
  credit with `details.extra.remedy_payment_authority_id` (also listed by
  `GET /v1/payments/authorities`). Replaying the same signed payment is
  refused with 402 `PAYMENT_AUTH_FAILED`, and a fresh x402 signature needs a
  fresh quote, which an autonomous account can take only after this one
  expires. Prefer the tool's own multi-document batching
  (`submit.py A.json B.json C.json`) over launching parallel processes — a
  burst of concurrent submissions is what trips the queue limit.
- **HTTP 429 `RATE_LIMITED` with `details.extra.bucket ==
  "fresh_execution_tasks"`**: the account has created its hourly allowance
  of new jobs (30 per clock hour by default; the window is fixed, not
  sliding). The quote already succeeded and stays valid. Read
  `details.extra.authorization_consumed`. When it is absent or `false`, wait
  `details.extra.retry_after_seconds` and retry the identical job request
  with the same idempotency key; pace a batch of more than 30 problems
  across hours rather than retrying in a loop. When it is `true` (an x402
  payment that settled before the refusal) the settled amount is credited to
  the account: after `details.extra.retry_after_seconds`, resubmit the same
  job request (same quote, same idempotency key) paying from account credit
  with `details.extra.remedy_payment_authority_id` (also listed by
  `GET /v1/payments/authorities`); a fresh x402 signature needs a fresh
  quote, which an autonomous account can take only after this one expires.
- **HTTP 409 after a 429**: if a byte-identical retry answers 409, do not
  invent a new idempotency key to get around it — report the error
  envelope verbatim; the pairing is a platform defect, not an input
  error.
