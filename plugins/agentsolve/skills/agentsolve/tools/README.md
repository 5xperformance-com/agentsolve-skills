# Tools

Three standard-library command-line tools for native instance files:

- `solve.py` — the one-invocation path: translate -> quote -> fund ->
  submit -> poll -> write in a single foreground call. Native files are
  translated first, canonical `*.canonical.json` documents pass through
  unchanged, and every `submit.py` option applies. The call finishes with
  the receipt-backed answer block, so nothing needs to be tailed, polled,
  or re-read afterwards.
- `translate.py` — deterministic translation of TSPLIB (`.tsp`/`.atsp`),
  CVRPLIB (`.vrp`), MPS (`.mps`/`.mps.gz`), PSPLIB single-mode (`.sm`), and
  Taillard JSSP files into canonical submission documents. Generated from the
  AgentSolve production translators; do not edit by hand. Dialects outside the
  accepted subset are rejected, never approximated. When translating
  standalone, review the written `*.canonical.json` before submitting it
  with `submit.py`.
- `submit.py` — drives one submission document through quote -> job -> poll
  and writes results named after the source instance (`berlin52.tsp` ->
  `berlin52.result.json`, plus a TSPLIB `berlin52.tour` for `1.1.tsp` and a
  CVRPLIB `berlin52.sol` for `1.2.vrp.cvrp`). `--out-dir` writes them where
  your task expects; the default is the document's own directory. Routing:
  default is the quote's default candidate; `--portfolio` runs every
  eligible candidate (up to 10, at cohort-size times the price) for
  find-the-best tasks — the tool polls the cohort to aggregate completion
  with N/M progress, obtains each settled member's result separately as its
  own attributed artifact (`FILE.<solver>.result.json` with the member's
  receipt), and emits the best by objective sense as the headline answer
  (`--settled-threshold N` takes the best of the first N responses);
  `--select` takes `solver_admission_id` values printed by the quote, not
  engine names; `--auto-route` is the other explicit alternative. Funding
  automation covers account-credit, trial-credit, Stripe, and faucet flows,
  each of which needs a claimed account. For x402 the tools sign nothing:
  when it is the only way to pay they write the quote's payment template to
  `STEM.x402.json` beside the results and exit with status 3. Have your
  wallet sign it in place, then re-run the same command with
  `--x402-payment STEM.x402.json`
  ([paying by x402](../references/reference-payment-x402.md)). Quotes last
  15 minutes unless `--quote-ttl-seconds` says otherwise. The
  [payment-rails reference](../references/reference-payment-rails.md)
  covers a claimed account's rails and a review-gated rail. Translated
  documents are written to the working directory, results to `--out-dir`.
  `STEM.result.json` holds the job read: the solution under `job.output`
  and the receipt under `job.routing_receipt`.

`python tools/solve.py --help` documents every flag. The tools' source is
not documentation: nothing in it is needed to run them.

Typical session:

```bash
python tools/solve.py instances/*.tsp --portfolio --out-dir solutions
```

Dialect coverage, vehicle-count rules, and per-format failure modes:
[../references/reference-native-formats.md](../references/reference-native-formats.md).
