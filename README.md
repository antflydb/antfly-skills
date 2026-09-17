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

The preview [Documentation Support Agent Guide](guides/support-agent/guide.md)
composes source ingestion, read-only retrieval, and an agent harness into a
grounded support experience.

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
| Foundations | [connect-antfly-mcp](skills/foundations/connect-antfly-mcp/SKILL.md), [query-antfly](skills/foundations/query-antfly/SKILL.md), [manage-antfly-indexes](skills/foundations/manage-antfly-indexes/SKILL.md), [troubleshoot-antfly](skills/foundations/troubleshoot-antfly/SKILL.md) |
| Connectors | [sync-github-to-antfly](skills/connectors/sync-github-to-antfly/SKILL.md), [sync-s3-to-antfly](skills/connectors/sync-s3-to-antfly/SKILL.md) |
| Harnesses | [configure-antfly-codex](skills/harnesses/configure-antfly-codex/SKILL.md), [configure-antfly-claude-code](skills/harnesses/configure-antfly-claude-code/SKILL.md), [configure-antfly-n8n](skills/harnesses/configure-antfly-n8n/SKILL.md), [configure-antfly-copilot](skills/harnesses/configure-antfly-copilot/SKILL.md), [configure-antfly-google-adk](skills/harnesses/configure-antfly-google-adk/SKILL.md) |
| Use cases | [build-antfly-support-agent](skills/use-cases/build-antfly-support-agent/SKILL.md), [build-antfly-workspace-agent](skills/use-cases/build-antfly-workspace-agent/SKILL.md) |

The [catalog](catalog.yaml) is the canonical inventory. Guides are human-facing
playbooks that compose Skills; they are read, not installed. The root
[SKILL.md](SKILL.md) is the flagship skill and router, and [references/](references/)
contains the shared reference corpus.

## Validation

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
node tools/verify-references.mjs
python3 scripts/validate_library.py
python3 scripts/scan_secrets.py
```

CI runs these checks and checks documented endpoints against Antfly's current
OpenAPI contract. Local endpoint checks require `ANTFLY_OPENAPI`; see
[CONTRIBUTING.md](CONTRIBUTING.md) for details and shell-script checks.
Static checks do not establish live integration compatibility.

## Contributing and support

Read [CONTRIBUTING.md](CONTRIBUTING.md) to propose or validate changes. Report
bugs and request features in [issues](https://github.com/antflydb/antfly-skills/issues).
Follow [SECURITY.md](SECURITY.md) for sensitive reports.

See the [roadmap](docs/roadmap.md) for planned directions and
[migration notes](docs/migration.md) if you use the older support-agent templates.

## License

[MIT](LICENSE). Referenced Antfly products and external Starters have their own licenses.
