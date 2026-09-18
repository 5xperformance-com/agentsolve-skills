# Input Size Limits

Inline canonical JSON payloads on `POST /v1/quotes` and on MCP calls must be
no larger than `64 MiB` after canonical encoding. Every other request body is
capped at `1 MiB`. A body over its cap is refused before authentication with
HTTP 413 `INVALID_PAYLOAD` and a `rejection_reason` of the form
`request exceeds <bytes> bytes`; a payload that only exceeds the inline limit
after canonicalization is refused by the quote with `field_name: "input"`.

Size the payload before submitting: encode it canonically and measure it.
Node names, distance matrices and per-pair cost lists dominate; an assignment
instance with 400 agents and 200 tasks is about 2.8 MiB, a CVRP instance with
251 customers about 0.9 MiB.

## Upload handles

Deployments may enable the API-origin upload path. Where it is enabled, an
input above the inline limit, or any input you prefer not to embed, goes
through a handle:

1. `POST /v1/inputs/presign` with `problem_type`, `problem_schema_version`,
   `allowed_regions`, and the commitments `content_sha256` and `size_bytes`
   computed over the canonical encoding of the payload. The response carries
   `input_handle` and `upload_url`; a declared size above the deployment's
   upload limit is refused with HTTP 413.
2. `PUT <upload_url>` with the JSON payload as the body. The response reports
   `state: "uploaded"` and `payload_sha256`; compare it with your commitment.
   A second upload to the same handle is refused with HTTP 409.
3. `POST /v1/quotes` with `input_handle` in place of `input`. The canonical
   problem hash is computed from the uploaded content, never from the handle.

Handles expire unused after 24 hours and their upload authorization after 15
minutes. Where uploads are disabled the presign route answers HTTP 503
`INPUT_UPLOAD_UNAVAILABLE`; keep the inline payload within the limit or reduce
the instance. The upload limit is the deployment's configured value and never
exceeds 64 MiB.
