# Tools

Two standard-library command-line tools for native instance files:

- `translate.py` — deterministic translation of TSPLIB (`.tsp`/`.atsp`),
  CVRPLIB (`.vrp`), MPS (`.mps`/`.mps.gz`), PSPLIB single-mode (`.sm`), and
  Taillard JSSP files into canonical submission documents. Generated from the
  AgentSolve production translators; do not edit by hand. Dialects outside the
  accepted subset are rejected, never approximated.
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
  `--select ID ...` and `--auto-route` are the explicit alternatives.
  Funding: account-credit authority, then trial credit, then Stripe
  (single-candidate cohorts only), with an automatic faucet fallback across
  drawable enrolled programs when no other rail is fundable.

Typical session:

```bash
python tools/translate.py instances/berlin52.tsp
python tools/submit.py instances/berlin52.tsp.canonical.json --out-dir solutions
```

Dialect coverage, vehicle-count rules, and per-format failure modes:
[../references/reference-native-formats.md](../references/reference-native-formats.md).
