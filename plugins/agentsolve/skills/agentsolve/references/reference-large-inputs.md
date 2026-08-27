# Input Size Limit

Inline canonical JSON payloads must be no larger than `1 MiB` after canonical
encoding. Larger inputs are not accepted in the current public posture.

Upload handles are disabled outside local development until governed
object-payload storage passes its separate security, residency, deletion, and
provider-qualification gate. Do not call `POST /v1/inputs/presign`,
`PUT /v1/inputs/{input_handle}`, or `agentsolve.uploads.create_handle` in a
public workflow.

Keep the inline payload within the limit or reduce the instance before quote
creation. A future activation will publish a new direct-upload workflow and
its exact limits; the disabled API-origin proxy is not that workflow.
