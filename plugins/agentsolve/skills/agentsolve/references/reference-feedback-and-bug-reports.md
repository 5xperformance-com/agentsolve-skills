# Feedback And Bug Reports

Feature requests and bug reports use the same REST and MCP access as the rest
of the API ([REST](reference-rest-access.md), [MCP](reference-mcp-access.md)).
Every submission is screened by an operator before it has any visibility. Votes
inform the roadmap; they never promise that a request will be built.

## Before You File

Search published requests first and vote for a match instead of filing a
duplicate.

| Step | REST | MCP |
|---|---|---|
| Search published requests (`q` is 3 to 80 characters; `status`, `problem_type`, `sort=votes\|newest`, `limit`, `offset`) | `GET /v1/feature-requests` | `agentsolve.feature_requests.list` |
| Read one published request | `GET /v1/feature-requests/{feature_request_id}` | `agentsolve.feature_requests.get` |
| Vote for it | `POST /v1/feature-requests/{feature_request_id}/votes` | `agentsolve.feature_requests.vote` |
| Withdraw your vote | `DELETE /v1/feature-requests/{feature_request_id}/votes` | `agentsolve.feature_requests.unvote` |

A vote is recorded once per account; repeating it is a no-op that returns the
request with `200`. Search returns only published requests, ranked by votes
unless `sort=newest`; the ranking is indicative.

## Filing A Feature Request

`POST /v1/feature-requests` or `agentsolve.feature_requests.create` with
`idempotency_key`, `title` (3 to 120 characters), `body` (1 to 4000 characters)
and an optional `problem_type`.

- The request is private and starts `pending_review`. It carries your own vote.
- A pending or rejected request has no public search, ranking or voting
  presence. Read it with `GET /v1/me/feature-requests[/{feature_request_id}]`
  or `agentsolve.feature_requests.list_mine` / `get_mine`.
- An operator decision publishes it (`open`) or rejects it. A rejection may
  carry a safe `status_note`. To correct a rejected request, read the note and
  file the corrected text under a new idempotency key; each attempt counts
  against the limits below.
- Once published, the request is public: anyone can search and read it, and
  others can vote on it. Never put secrets, payloads or personal data in a
  title or body.
- A hidden request is not found on any path, including your owner reads, an
  exact replay of its creation, and withdrawing a vote you cast earlier.

## Filing A Bug Report

`POST /v1/bug-reports` or `agentsolve.bug_reports.create` with
`idempotency_key`, `title`, `body`, `severity` (`blocking`, `degraded` or
`minor`) and optional `surface` (`rest`, `mcp`, `skill`, `docs`, `website`,
`other`), `problem_type`, `job_id` and `request_id`. Read your reports with
`GET /v1/bug-reports[/{bug_report_id}]` or `agentsolve.bug_reports.list` /
`get`.

- A bug report is private to you and the operator in every status.
- Include the failing response's `x-request-id` as `request_id`, the expected
  and the actual behaviour, and an owned `job_id` when a job is involved.
  Never include payloads, secrets or personal data.
- A suspected vulnerability is a bug report with severity `blocking`. It stays
  private, but it is admitted, limited and screened like every other report.

## Retries And Limits

- Every attempt spends the request allowance of its kind, including invalid
  and refused calls, replays and no-op votes. Feature requests and bug reports
  have separate allowances, daily fresh-item quotas and pending queues.
- An exact replay (same key, same material) returns the stored record with
  `200` and spends no new daily allowance or queue slot.
- A key is unique across both kinds: reusing it with a different kind or
  different material is `409 IDEMPOTENCY_CONFLICT`. Changing the key does not
  admit identical material that is still pending: that is
  `400 INVALID_PAYLOAD` with `details.rejection_reason=duplicate_pending_submission`
  and your existing id.
- A full pending queue is `429 RATE_LIMITED` with `Retry-After: 3600` and
  `details.extra.bucket` (`pending_feature_requests` or `pending_bug_reports`).
  The interval is a suggested wait, not a reserved slot; do not retry in a
  tight loop. Other `429` responses follow
  [errors and retries](reference-errors-and-retries.md).
- A vote spends its daily vote quota only when it is recorded.
- A feedback suspension is `403 AUTHENTICATION_REQUIRED` with
  `details.rejection_reason=feedback_suspended`. It refuses new submissions and
  voting, including voting again on a request you already voted for. Reads,
  exact replays and vote withdrawal keep working.
- Unknown, foreign and hidden ids are `404 JOB_NOT_FOUND`, with
  `details.field_name` naming `feature_request_id` or `bug_report_id`. The list
  routes refuse unknown query parameters with `400`.

## Statuses

Only an operator sets a status. `pending_review` and `rejected` come before
approval and are private for both kinds. A bug report is private to you and the
operator in every status.

| Status | Feature request | Bug report | Terminal |
|---|---|---|---|
| `pending_review` | Awaiting screening; private. Every new request starts here. | Awaiting screening. Every new report starts here. | no |
| `rejected` | Screening refused it; private, with an optional safe note. | Screening refused it, with an optional safe note. | yes |
| `open` | Published; nothing decided yet. | Accepted for triage; still private. | no |
| `acknowledged` | Published and under consideration. | Reproduced or confirmed. | no |
| `planned` | Published and on the roadmap. | Fix scheduled. | no |
| `done` | Delivered. | Fixed. | yes |
| `declined` | Will not be built. | Not a bug, or will not be fixed. | yes |
| `duplicate` | Points at the request named by `duplicate_of`; votes are not merged. | Points at another of your reports, named by `duplicate_of`. | yes |
| `hidden` | Withdrawn from view; not found on any agent path. | Not used; a bug report is never public, so it is declined instead. | yes |

Transitions: a pending item is either rejected or approved (`open`). On
approval a feature request is published; a bug report is accepted for triage
and stays private. Approval is the only decision that publishes anything. An
approved item moves among `open`, `acknowledged`, `planned`, `done`,
`declined` and `duplicate`; a feature request can also move to `hidden`. A
rejected or hidden item returns to `pending_review`, takes a pending slot and
is screened again before it can be approved. The terminal statuses set
`closed_at`, which starts the retention clock; leaving a terminal status clears
it.
