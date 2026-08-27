# Degraded Modes And Non-Guarantees

`degraded_mode` explains supply or routing limitations. `single_source` means
only one eligible source remains. `single_source_first_party` means the result
is served by the first-party path. `no_supply` means no eligible supply for the
requested policy.

Do not treat degraded mode as a hidden failure when the quote and receipt say it
is acceptable under caller policy. Do not hide it either; surface the limitation
before the user acts on the result.

Solver supply can change after admission reviews. Treat new families as
provider-neutral execution supply exposed through menu, quote, policy, and
receipt fields; do not alter canonical payloads or ask for solver-native input
syntax.

Stage 0 non-guarantees:

- no global optimality claim unless exact certification exists
- no runtime, quality, or capacity guarantee from a complexity-tier label;
  an open-ended L region is only a catalog price segment
- no support claim for every optimization or inference domain
- no provider-hosted privacy or enclave-backed execution claim
- no decentralization or governance-by-stake claim
- no zero-variance latency or price forecast claim

Treat `optimality_certified`, `optimality_gap`, `proved_optimal`, and warning
blocks as diagnostics. On quotes, inspect `estimate_basis` and
`evidence_scope_state`; on receipts, inspect `established_guarantee`. Read
authoritative claims with
[reference-verification-and-certificates.md](reference-verification-and-certificates.md).
