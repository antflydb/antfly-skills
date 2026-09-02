# Antfly Guides and Skills Library

Use `SKILL.md` as the compatibility router and `catalog.yaml` as the canonical
library inventory.

## Artifact model

- `guides/`: complete outcome packages with human-facing content and machine-readable composition manifests.
- `skills/foundations/`: reusable Antfly operations.
- `skills/connectors/`: source-connector setup and verification.
- `skills/harnesses/`: agent-runtime configuration and security boundaries.
- `skills/use-cases/`: business outcomes that compose other Skills.
- `schemas/`: catalog contracts.
- `scripts/`: library validation.

Read a selected SKILL.md completely before editing or following it. Keep Skill
frontmatter to `name` and `description`, use verb-led hyphen-case names, keep
detailed variant material in one-level references, and validate with:

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate_library.py
python3 scripts/scan_secrets.py
```

Preserve read-only defaults for retrieval agents, discover current MCP
capabilities instead of hard-coding counts, and never commit credentials.
