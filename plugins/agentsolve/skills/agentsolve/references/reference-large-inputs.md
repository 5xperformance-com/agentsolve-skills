# Large Inputs

Inline canonical JSON payloads must be no larger than `1 MiB` after canonical
encoding. Larger inputs use upload handles rather than embedding payloads in
REST requests or MCP messages.

## Flow

1. Request an upload handle with `POST /v1/inputs/presign` or
   `agentsolve.uploads.create_handle`.
2. Upload the canonical JSON out of band to the returned handle.
3. Create the quote by referencing the uploaded object handle while preserving
   `problem_type`, `problem_schema_version`, and canonical problem hashing.
4. Validate before quote creation; invalid input is not billable.

The canonical problem hash is computed from canonicalized payload content, not
from the upload URL or handle string. REST and MCP use the same underlying
object-handle contract.
