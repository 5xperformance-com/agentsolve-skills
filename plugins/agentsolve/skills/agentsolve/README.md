# Stage 0 Adoption Corpus

The authored Stage 0 adoption source lives at
`docs/adoption/stage0/source/`. This README is mirrored into the projection
targets so every copy states the same source-of-truth rule.

Committed projections are generated for:

- `skills/agentsolve/`
- `docs/adoption/stage0/bundle/`

Directory convention:

- `SKILL.md`: concise progressive-disclosure entrypoint.
- `references/`: one-hop references linked directly from `SKILL.md`.
- `examples/`: runnable quote -> job -> poll examples with deterministic
  dry-run output for CI and optional local integration execution.
- `tests/`: skill-local golden fixtures when later tickets add examples.
- `manifest.json`: projected bundle inventory and publication metadata.

Projection and validation:

- Run `python scripts/adoption_stage0_lint.py --project` after editing source.
- Run `python scripts/adoption_stage0_lint.py --check` before review.
- Runtime skill packages must not contain validation transcripts, release
  audit reports, or owner sign-off evidence.
- Release and versioning rules live outside the runtime package at
  `docs/adoption/stage0/release-and-versioning.md`.

Release tags use:

```text
agentsolve-stage0-adoption-cpl-v<canonical-language-version>-v<adoption-semver>
```
