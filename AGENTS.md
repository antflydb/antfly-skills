# Antfly Guides and Skills Library

`SKILL.md` is the flagship skill and router; `catalog.yaml` is the canonical
library inventory; `references/` is the shared, CI-verified fact core.

## Artifact model

- `guides/`: playbooks — complete outcome packages with human-facing content and machine-readable composition manifests (read, not installed).
- `skills/foundations/`: reusable Antfly operations.
- `skills/connectors/`: source-connector setup and verification.
- `skills/harnesses/`: agent-runtime configuration and security boundaries.
- `skills/use-cases/`: business outcomes that compose other Skills.
- `references/`: the verified reference corpus (backend, frontend, ops).
- `schemas/`: catalog contracts.
- `scripts/` and `tools/`: library and fact validation.

Read a selected SKILL.md completely before editing or following it. Keep Skill
frontmatter to `name` and `description`, use verb-led hyphen-case names, keep
detailed variant material in one-level references, and validate with:

```bash
node tools/verify-references.mjs
python3 scripts/validate_library.py
python3 scripts/scan_secrets.py
```

Facts must be verified against the current Antfly source before they ship —
the implementation outranks spec prose. Preserve read-only defaults for
retrieval agents, discover current MCP capabilities instead of hard-coding
counts, and never commit credentials.
