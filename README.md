# antfly-skills

Antfly skills for AI coding agents, installable with the
[skills CLI](https://skills.sh):

```bash
npx skills add antflydb/antfly-skills
```

That installs the flagship `antfly` skill — verified, CI-checked knowledge of
Antfly's APIs, query shapes, React components, and operations, which also
routes agents to the focused Skills below. Install a focused Skill directly
with `npx skills add antflydb/antfly-skills --full-depth --skill <name>`.
Already installed? `npx skills update` pulls the latest corpus.

The first preview Guide is `support-agent`. Its reusable behavior
is migrated from `antflydb/support-agent-templates`, with portable evaluations
and the Claude direct-chunk regression preserved as separate suites.

The experimental [Google Workspace Agent Guide](guides/workspace-agent/guide.md) covers
Workspace setup, ingestion into Antfly and an MCP connection to the chosen agent runtime.
Drive, Gmail, Meet and Calendar are source options. Graph enrichment is optional and has
its own readiness checks. The current pilot covers selected Gmail/Drive/Meet snapshots;
Calendar and continuous sync are not yet implemented.

The experimental [Google Agent Guide](guides/google-agent/guide.md) covers Google ADK,
Gemini on Vertex AI, Antfly MCP retrieval and optional private Cloud Run deployment.
It composes with the Workspace Guide or another ingestion workflow.

## Library

| Category | Packages |
| --- | --- |
| Foundations | `connect-antfly-mcp`, `query-antfly`, `manage-antfly-indexes`, `troubleshoot-antfly` |
| Connectors | `sync-github-to-antfly`, `sync-s3-to-antfly` |
| Harnesses | `configure-antfly-codex`, `configure-antfly-claude-code`, `configure-antfly-n8n`, `configure-antfly-copilot`, `configure-antfly-google-adk` |
| Use cases | `build-antfly-support-agent`, `build-antfly-workspace-agent` |

See `catalog.yaml` for machine-readable composition and `guides/` for complete
Guide manifests and the human-facing experience. The root `SKILL.md`
and `references/` remain
available as a compatibility entrypoint while consumers migrate to focused
skills.

## Validate

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate_library.py
python3 scripts/scan_secrets.py
```

Validation checks the catalog and Guide manifests against their JSON Schema,
Skill frontmatter, referenced packages and resources, and required UI metadata.

Guides under `guides/` are playbooks: complete outcome compositions an agent
reads and executes — they are not installable skills. Each corresponds to a
human guide on [antfly.io/docs](https://antfly.io/docs/guides).

## Validation

Both checks run in CI and locally:

```bash
node tools/verify-references.mjs        # fact harness (against openapi.yaml in CI)
python3 scripts/validate_library.py     # packaging / catalog contract
```

Replace `{{ANTFLY_API_URL}}` in the files if you want the packaged examples to
point at a specific Antfly deployment.
