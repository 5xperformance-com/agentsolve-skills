# Problem Type: Staff Rostering

Canonical schema versions:

- Input: `4.3.scheduling.rostering.input.v3`
- Output: `4.3.scheduling.rostering.output.v2`

Use `4.3.scheduling.rostering` for one-site dated staff-slot assignment with
hard skill coverage, availability, overlap, rest, hours, and consecutive-day
rules, minimizing exact integer target and fairness penalties.

## Formulation Recipe

- `site_timezone` is an IANA zone used for local-day and weekend attribution.
- Slot instants are UTC; durations are instant differences, with partial hours
  rounded up for hours-based rules.
- `is_night` is caller-declared.
- `skill_substitution` is an optional list of `[from, to]` pairs declaring that
  a member holding `from` can also cover `to`. Substitution is one-hop and
  directional, so each member's effective skills are their own skills plus the
  skills directly substitutable from them. Omit it for exact-skill coverage.
- A `(staff_id, slot_id)` assignment covers the one slot requirement matching
  that member's effective skills.
- Because assignments do not name a role, every member may match at most one
  required skill in a slot, so coverage stays keyed on a single skill per
  staff-slot pair and the roster remains an exact integer model.
- `min_headcount` is hard; `target_headcount` and staff targets are soft.
- `min_hours` is a contracted-hours floor beside the `max_hours` cap: hours a
  member must reach, not only hours they may not exceed.
- Repairing a published roster: `pinned_assignments` must appear in the result,
  `forbidden_assignments` must not, `baseline_roster` names the plan being
  revised, and `penalties.churn` prices each difference from it in either
  direction. A pin the hard rules already forbid is rejected as an infeasible
  instance rather than treated as a hint.
- `assignment_costs` charges an integer cost when a `(staff_id, slot_id)` pair
  is assigned, so an unwelcome-but-legal shift can be priced instead of banned.
- The price tier uses `staff_count * slot_count` — `S` <= 750,
  `M` 751–12,000, `L` >= 12,001 — but measured evidence also depends on
  eligible-pair and skill density, coverage structure, and potential rest
  conflicts. An open-ended L tier is not an unlimited-capacity claim.

## Deferrals

| Required semantic | Action |
|---|---|
| one worker may fill several required roles in one slot | code `rostering_explicit_skill_assignment`; nearest supported subset has one matching role per staff-slot pair, including when substitution makes a member's effective skills cover two required skills in one slot |
| employment contracts or wish lists | code `rostering_contract_model`; nearest supported subset uses explicit hard limits and targets |
| recurring patterns | code `rostering_shift_patterns`; nearest supported subset uses dated slots |
| bidding | code `rostering_preference_bidding`; nearest supported subset has no bids |
| several sites | code `rostering_multi_site`; nearest supported subset has one site |
| on-call states | code `rostering_on_call_states`; nearest supported subset is assigned or unassigned |
| rolling repair across horizons | code `rostering_rolling_rescheduling`; nearest supported subset repairs one fixed horizon using `baseline_roster`, `pinned_assignments`, and `penalties.churn` |

## Result Interpretation

The verifier checks every hard rule and recomputes the exact integer penalty.
That creates `valid_result`, not an independent optimality certificate.
`solver_proved` requires an explicit admitted-solver optimal result.

An infeasible result settles only when the verifier's bounded reference search
confirms it. A size or search limit leaves the claim unconfirmed and invalid.

`verify_only` requires `candidate_roster`; `optimize` forbids it.
