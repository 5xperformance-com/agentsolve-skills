# Solver Track Records

Contents: Access · When To Look Up · Reading A Grid · Default Effort · Quotes And Qualification Runs · Customer Statistics · When A Portfolio Is Better

## Access

One verified job unlocks every solver's track record for your account.
Until then a quote shows run counts and tested sizes only; the job unlocks
the ranks, quality and run times.

- **Open to anyone:** the class list, `GET /v1/leaderboards`, or
  `agentsolve.leaderboards.get` with no `problem_class`. It names each
  class's grids (`family_id`), its current `snapshot_id`, `methodology_url`,
  `solvers_route` and, under `access`, this rule as data. It holds no
  results.
- **Needs the job:** a class's results, `GET /v1/leaderboards/{problem_class}`,
  a stored snapshot at `/v1/leaderboards/{problem_class}/snapshots/{snapshot_id}`,
  or the tool with `problem_class` (and `snapshot_id`). Each needs scope
  `read`.
- **What counts:** a job on the account that settled with a result its
  class's verifier accepted, however it was paid. It still counts while
  `DISPUTED`, `REEXECUTING` or `SUPERSEDED`. A failed or `REFUNDED` job does
  not count, and neither does a quote. One job unlocks every class for every
  key and agent on the account and does not lapse; it ends only if every
  verified job on the account is refunded after an upheld dispute. An
  unclaimed agent qualifies on its own account.
- **The refusal:** an account without one gets 403 `AUTHENTICATION_REQUIRED`
  with `details.rejection_reason` `contribution_required` (over MCP, in
  `error.data.agentsolve_error`). The message states the rule and the next
  step; `details.extra` repeats the `access` block. Signing in again or
  repeating the bootstrap never cures it: create a quote with
  `POST /v1/quotes`, run one job until it is `SETTLED`, then ask again. If
  that job is refunded, run another. No credentials gives 401; a key without
  `read` gets the scope refusal naming `required_scopes`.
- **Caching:** over REST, results carry the snapshot id as `ETag`; send it
  as `If-None-Match` to get 304 when nothing changed.

## When To Look Up

- Choosing a solver for a class you run again: put the fitting row's
  `solver_admission_id` in `selected_algorithms`, when the quote offers it,
  instead of taking the default.
- Deciding between one solver and a portfolio (last section).
- After the class list shows a new `snapshot_id` for the class.

Until the account has a verified job, choose from the quote alone.

## Reading A Grid

A class's results hold the benchmark panel in `grids[]`, the release's
qualification runs in `qualification[]` and real customer jobs in
`customer`. The method, with every formula and limitation, is at
`methodology_url` (`https://agentsolve.io/docs/leaderboards`).

`grids[]` holds one grid per panel family. Every row (`solver_admission_id`,
`solver_slot`, `solver_version`) accepts every case of its grid, five per
published size tier, each run three times; the middle attempt is the
result. Read the grid whose family matches your instance. The method page
describes each family and lists each grid's capability constraints: if your
instance uses a feature its grid excludes, the ranks do not cover it.

- **Two ranks, never blended.** `quality_rank` and `time_rank` are each 1
  plus the number of rows better on that axis by more than the grid's
  `resolution`: `quality` for quality; for time, the larger of
  `absolute_seconds` and `relative` × the faster time. Rows are listed
  quality first.
- **Ties.** Equal ranks mean the difference is inside the resolution: treat
  the rows as equal on that axis. Several rows can share rank 1.
- **Frontier.** `frontier: true` marks a row unless another ranked row is
  at least as good on both ranks and better on one. Choose from the frontier:
  `quality_rank` 1 when the answer matters most, `time_rank` 1 when time
  does. Price (`panel_price_usdc`) is shown beside it, never folded in.
- **`rank_status`.** `ranked`; `single_row` (the only solver of its grid,
  no rank); `unranked` (fewer than two rankable rows); `pending` (results
  still to measure, shown partial). Only ranked rows carry ranks.
- **Verdict.** `verdict.kind` is checked in this order: `suppressed` (every
  case withheld after a verifier question), `single_row`, `pending`,
  `none_solved` (no row solved a case within the budget), `all_tied` (every
  ranked row at rank 1 on both axes), `quality_tied` (choose by time),
  `separated`. The lists `best_quality`, `fastest`, `frontier` and
  `pending` name admission ids; `sentence` says the same in words.
- **Row figures.** `quality` is the mean of Q = 1 / (1 + gap) over the
  grid's cases, unsolved counting 0; `solved` of `cases`;
  `verified_attempts` of `attempts` shows how often a single run succeeds;
  `proofs` and `proven_matches`; `mean_gap_percent`; `time_seconds`, a
  shifted geometric mean with an unsolved case at twice the budget; and
  `time_ratio` to the grid's fastest row. `measured_on` and `carried_over`
  say when the row was measured and whether it keeps the results of an
  unchanged earlier build of the same solver.
- **Tiers.** `tiers[]` repeats the row figures per size tier, without
  ranks. Read the tier of your quote's `complexity_tier`: a row ranked
  first overall can trail in your tier.
- **`ran_to_budget`.** Results whose run used the whole budget. A row with
  many searches until time runs out, so more time may help it; a row with
  none stopped on its own rule.
- **Head-to-head.** `head_to_head[]` gives `first`'s record against
  `second`: `shared`, `wins`, `ties`, `losses`, a win only beyond the
  quality resolution.
- **Per case.** `results[]`: `status` (`solved`, `unsolved`, `pending`),
  `quality`, `gap_percent`, `time_seconds`, the three `attempts` and the
  middle attempt's `receipt_id`.

## Default Effort

Panel results are for the default request: no `solver_hints`, the included
solve budget. Each solver stops by its own default rule, so ranks compare
default effort. Each row shows its measured effort: `run_seconds_median`
and `run_seconds_max` over `run_seconds_count` results. A hint such as
`time_limit_seconds` changes some solvers' effort and not others', so a
hinted job may not match its row. The method page lists each solver's
default stopping rule.

## Quotes And Qualification Runs

A quote's evidence summary carries run counts and tested sizes, never a
rank, time or quality figure. A candidate whose
`evidence_summary.evidence_state` is `qualification_only` had one verified
qualification run in the quoted size region: `qualification_observation_count`
is 1, `tested_size_regions` lists where it qualified, `tested_feature_envelope`
bounds the tested case, the caveat is `qualification_only_evidence`, and no
band is set. `evidence_scope_state` `inside_measured_evidence` means your
instance lies inside that envelope, and `outside_measured_evidence` that it
does not, for example because it is larger than the tested case. It shows
the solver works there, not that it ranks well. `declared_only` means no run
in the region.

`qualification[]` in the results holds those runs per delivery grid: per
case and row `verified`, `gap_percent`, `proven`, `run_seconds` and
`terminated_reason`, without ranks. They ran under another protocol and are
never compared with the panel.

## Customer Statistics

`customer` covers the last `window_days` (90) of customer jobs.
`customer.rows[]` gives each solver's `outcomes` and `run_times`;
`customer.head_to_head[]` gives each pair's `first`, `second` and `cell`.
Each statistic is `{"value": {…}, "as_of": "YYYY-MM-DD"}` or
`{"value": null}`. Under `value` sit `problems` and `solved` (outcomes),
`run_seconds_median` and `run_seconds_p90` (run times, solved problems only),
or `shared`, `wins`, `ties` and `losses` (a cell, from `first`'s side).

- They describe what customers chose to send each solver, so one row's
  figures are not comparable with another's: one solver may see harder
  problems. Compare solvers with `head_to_head` on shared problems, never
  row against row.
- Each solver counts one result per distinct problem; platform faults never
  count against it.
- Null means not shown, and the reason is not given. A value can lag recent
  jobs; `as_of` dates it.
- They are never ranked or mixed with the panel.
- Your own jobs count too, unless your account objects: how each solver
  performed, never the problem itself. A portfolio keeps you the winner and
  adds to `head_to_head`.

## When A Portfolio Is Better

A portfolio puts 2 to 10 quoted `solver_admission_id` values in
`selected_algorithms`. Each member runs on your instance and is verified
and settled on its own; you keep the best
([polling](reference-polling-and-backoff.md)). Its price is the sum of its
members' prices, and it needs a claimed account paying by account credit
or trial credit. Prefer it when the record cannot pick one solver for your
instance:

- a `head_to_head` cell between two rows with `quality_rank` 1 has both
  `wins` and `losses` above 0, even in an `all_tied` grid;
- your instance uses a feature your grid excludes;
- the verdict is `suppressed` or `pending`.

Otherwise pin one solver: a row with `quality_rank` 1, or the row with the
best `quality` in your tier if that is another; break a tie by `time_rank`
or price.
