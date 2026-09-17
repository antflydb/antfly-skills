# Migration from support-agent-templates

Use this library for the reusable support-agent behavior and harness setup
previously packaged in `antflydb/support-agent-templates`. The Support Agent
Guide remains in preview; validate your chosen harness before switching.

## Mapping

| Existing asset | New canonical location |
| --- | --- |
| Shared retrieval contract | `skills/use-cases/build-antfly-support-agent/references/retrieval-contract.md` |
| Read-only tool policy | `skills/use-cases/build-antfly-support-agent/references/read-only-policy.json` |
| Portable evaluations | `skills/use-cases/build-antfly-support-agent/assets/support-agent-evals.json` |
| Claude direct-chunk regression | `skills/use-cases/build-antfly-support-agent/assets/claude-code-regression-evals.json` |
| Codex adapter | `skills/harnesses/configure-antfly-codex/` |
| Claude Code adapter | `skills/harnesses/configure-antfly-claude-code/` |
| n8n adapter | `skills/harnesses/configure-antfly-n8n/` |
| Copilot adapter | `skills/harnesses/configure-antfly-copilot/` |
| Knowledge Support / Next.js applications | Starters referenced by the Support Agent Guide |

## Migrating a project

1. Read the [Support Agent Guide](../guides/support-agent/guide.md).
2. Install the focused Skills for your source connector and agent harness.
3. Carry over your table, index, citation mapping, and escalation settings.
   Keep credentials in the environment or harness secret store.
4. Run the portable evaluations and applicable harness regression checks before
   replacing the existing integration.

The Knowledge Support and Next.js applications remain separate Starters for
projects that need a hosted UI.

## Existing installs

The flagship `antfly` skill keeps its name and location. Run `npx skills update`
to update an existing installation. Focused Skills are optional additions; see
[the README](../README.md) for installation commands.
