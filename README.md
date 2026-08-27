# agentsolve-skills

Publicly installable agent skills for [AgentSolve.io](https://agentsolve.io), the marketplace
where AI agents buy verified answers to hard computational problems.

The `agentsolve` skill teaches a coding agent the whole platform in one progressive-disclosure
package: how to classify a request into a problem class, draft canonical input, run the
`quote → job → poll` flow over REST or MCP, satisfy payment requirements, and interpret receipts,
without ever touching a solver-native format.

## What's inside

```
plugins/agentsolve/skills/agentsolve/
├── SKILL.md          # entrypoint: happy path, launch classes, guardrails
├── references/       # 31 one-hop references: class selection, per-class guides,
│                     # methods, formulation patterns, REST/MCP/payments/receipts
├── examples/         # 12 runnable quote → job → poll examples, one per launch
│                     # class, each with a deterministic --dry-run
└── manifest.json     # bundle inventory and publication metadata
```

The package is generated from AgentSolve's governed adoption corpus and versioned with the
canonical problem language it teaches (current adoption version: 0.13.0).

## Install

### Claude Code (plugin marketplace)

```
/plugin marketplace add 5xperformance-com/agentsolve-skills
/plugin install agentsolve@agentsolve-skills
```

### Any harness that reads SKILL.md folders

```bash
git clone https://github.com/5xperformance-com/agentsolve-skills
cp -r agentsolve-skills/plugins/agentsolve/skills/agentsolve ~/.claude/skills/agentsolve
# or into your project's .claude/skills/
```

## Try it without credentials

Every example has a deterministic dry-run mode:

```bash
python plugins/agentsolve/skills/agentsolve/examples/run_tsp.py --dry-run
```

Point the same script at the live API with `--base-url` (or `AGENTSOLVE_BASE_URL`).

## Links

- Website & docs: https://agentsolve.io/docs
- Machine-readable guide: https://agentsolve.io/llms-full.txt
- Frozen contract artifacts: https://agentsolve.io/openapi.json · https://agentsolve.io/mcp-tools.json
