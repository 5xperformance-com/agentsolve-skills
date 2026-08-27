# Native instance formats

`tools/translate.py` deterministically translates common native optimization
file formats into canonical submission documents on the client side. The
quote API accepts canonical input only; translation always happens before the
quote, never inside it. Dialects outside the accepted subset are rejected
with a named error, never approximated — when a file is rejected, write the
canonical payload directly using the matching problem-type reference.

## Coverage

| Format id | File types | Problem class | Accepted subset |
| --- | --- | --- | --- |
| `tsplib` | `.tsp` | `1.1.tsp` | `EDGE_WEIGHT_TYPE` `EUC_2D`, `GEO`, or `EXPLICIT` with `FULL_MATRIX` or `LOWER_DIAG_ROW` |
| `tsplib` | `.atsp` | `1.1.tsp` | `EXPLICIT` with `FULL_MATRIX` (asymmetric distances preserved) |
| `cvrplib` | `.vrp` | `1.2.vrp.cvrp` | `EUC_2D` or `EXPLICIT` with `LOWER_ROW`; exactly one depot |
| `mps` | `.mps`, `.mps.gz` | `2.1.lp` or `2.2.milp` | `NAME`/`ROWS`/`COLUMNS`/`RHS`/`BOUNDS`/`ENDATA`; one objective row; linear `L`/`E`/`G` rows; integer markers; `LI`/`UP` bounds |
| `psplib-sm` | `.sm` | `4.1.scheduling.rcpsp` | single-mode instances whose resources are all renewable |
| `taillard` | header-sniffed text | `4.2.scheduling.jssp` | standard Taillard job-shop files; pick one instance with `--instance-index` |

Files with other extensions are recognized by header sniffing; pass
`--format` to override detection.

Active input schema versions written by the translator: `1.1.tsp.input.v1`,
`1.2.vrp.cvrp.input.v4`, `2.1.lp.input.v2`, `2.2.milp.input.v2`,
`4.1.scheduling.rcpsp.input.v3`, `4.2.scheduling.jssp.input.v3`.

## Format rules worth knowing

- TSPLIB distance semantics follow the published specification: `EUC_2D`
  rounds to the nearest integer and `GEO` uses the published geographical
  formula, so translated objectives match published optima.
- CVRPLIB vehicle count is taken from the `VEHICLES` header, then a
  `No of trucks` comment, then an explicit `--vehicle-count`; it is never
  guessed. A file with none of the three is rejected.
- MPS routes to `2.2.milp` when any variable is integer and to `2.1.lp`
  otherwise; sections outside the accepted subset (for example `RANGES`)
  are rejected.
- Taillard files may hold several instances; translation targets exactly one.

## Identifier fidelity

Source identifiers become canonical identifiers at translate time, so results
read back in source terms without a mapping file: MPS column and row names,
PSPLIB job numbers, and Taillard job and operation order are preserved
(Taillard machine ids convert from 1-based to `m0..`). TSPLIB and CVRPLIB
nodes are numbered `n1..nDIM` in file order, and the submission document's
`node_numbering` field records that order.

## Native solution files

`tools/submit.py` names outputs after the source instance recorded in the
submission document (`berlin52.tsp` -> `berlin52.result.json`) and writes
them to `--out-dir` (default: the document's directory) — point it at the
directory your task expects. For `1.1.tsp` it additionally writes a TSPLIB
`berlin52.tour`, and for `1.2.vrp.cvrp` a CVRPLIB `berlin52.sol`, using the
submission document's `node_numbering`. Other classes read their results
from the `result.json` in the identifier terms above. The Stripe fallback
requires an already-confirmed PaymentIntent
(`AGENTSOLVE_STRIPE_PAYMENT_INTENT_ID`); an unconfirmed preflight intent
stops with an explicit confirmation handoff instead of submitting.

The remaining launch classes have no dominant community interchange format;
write their canonical payloads directly from the problem-type references.
