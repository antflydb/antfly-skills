# Antfly Guides and Skills Library

Reusable Guides, Agent Skills, and Starters for building with Antfly.

- **Guides** package and present a complete, testable customer outcome in the Antfly UI and documentation.
- **Skills** give an agent the procedures and guardrails needed to implement a Guide.
- **Connectors** move data into Antfly or expose Antfly to a harness.
- **Starters** are optional code or workflow assets copied into a project.

The first preview Guide is `support-agent`. Its reusable behavior
is migrated from `antflydb/support-agent-templates`, with portable evaluations
and the Claude direct-chunk regression preserved as separate suites.

## Library

| Category | Packages |
| --- | --- |
| Foundations | `connect-antfly-mcp`, `query-antfly`, `manage-antfly-indexes`, `troubleshoot-antfly` |
| Connectors | `sync-github-to-antfly`, `sync-s3-to-antfly` |
| Harnesses | `configure-antfly-codex`, `configure-antfly-claude-code`, `configure-antfly-n8n`, `configure-antfly-copilot` |
| Use cases | `build-antfly-support-agent` |

See `catalog.yaml` for machine-readable composition and `guides/` for complete
Guide manifests and the human-facing experience. The original root `SKILL.md`
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
