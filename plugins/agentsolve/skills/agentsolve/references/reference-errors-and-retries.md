# Errors And Retries

All agent-facing failures use the stable V5 error envelope with `code`,
`message`, `retryable`, `idempotency_relevant`, and redacted `details`.

## Error Code Inventory

| Code | Typical handling |
|---|---|
| `PROBLEM_NOT_SUPPORTED` | Reclassify or defer before quote creation. |
| `NO_ELIGIBLE_SOLVER` | Adjust policy or try later if supply changes. |
| `INVALID_PAYLOAD` | Correct canonical input; do not retry unchanged. |
| `INTERNAL_ERROR` | Retry only when `retryable=true`; preserve idempotency key. |
| `QUOTE_EXPIRED` | Create a fresh quote. |
| `PAYMENT_AUTH_FAILED` | Correct funding path or ask caller to reauthorize. When `details.extra.retry_after_seconds` is present (velocity windows span hours), wait that long — do not retry on minutes-scale backoff. |
| `JOB_NOT_FOUND` | Check account scope and job ID. |
| `IDEMPOTENCY_CONFLICT` | Do not reuse the key for different material inputs. |
| `QUOTE_HINTS_MISMATCH` | Pass the quote's `effective_solver_hints` verbatim on the job, or create a new quote. |
| `INVALID_JOB_STATE` | Follow the lifecycle; do not force the transition. |
| `ROUTING_MODE_NOT_SPECIFIED` | Include exactly one routing mode on job creation. |
| `ROUTING_MODE_AMBIGUOUS` | Send only one of `auto_route` / `selected_algorithms`. |
| `COHORT_SIZE_EXCEEDED` | Portfolio jobs take at most 10 solver admission ids. |
| `MODE_3_NO_ELIGIBLE_CANDIDATE` | Relax the policy or select a solver explicitly. |
| `CONCURRENT_QUOTE_CONSUMPTION` | Poll or retry with the same idempotency key. |
| `AUTHENTICATION_REQUIRED` | Refresh credentials. |
| `ORIGIN_NOT_ALLOWED` | Use an allowed MCP or REST origin. |
| `RATE_LIMITED` | Back off according to server guidance. |

Typed quote rejections should be interpreted before retry. If the rejection is
a typed deferral, return the deferral code, nearest supported subset, and
roadmap status rather than approximating the user's requirement.
