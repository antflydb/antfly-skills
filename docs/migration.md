# Migration from support-agent-templates

`antflydb/support-agent-templates` at public-main commit `ab85564` remains the
verified source for the existing harness implementations during preview. Local
commit `41ab932` provides useful outcome-packaging research but is not merged
into public `main`; its competing terminology is not adopted here.

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

## Graduation

1. Validate the four migrated harness Skills with live read-only Cloud keys.
2. Run the portable evaluation suite against each harness.
3. Add automated MCP contract-drift and permission-boundary tests.
4. Mark the Support Agent Guide `verified` and record supported versions.
5. Migrate the remaining harness adapters based on customer demand.
6. Archive or redirect the template repository only after canonical parity is proven.

Do not duplicate updates across both repositories indefinitely. During preview,
record the source commit in the Guide manifest and periodically reconcile it.

## Existing installs

Nothing breaks for anyone who already ran `npx skills add antflydb/antfly-skills` —
the root skill keeps its name and location. Run `npx skills update` to pull the
current, corrected reference corpus.
