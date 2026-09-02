# Antfly Guides and Skills Library

Use `SKILL.md` to route an Antfly task to the smallest Skill in `skills/`.
Use `catalog.yaml` and `guides/` to compose customer outcomes.

Read the chosen SKILL.md completely and load only its required references.
Do not treat the legacy root reference tree as the source of truth for exact
commands, endpoint paths, authentication, or MCP tool counts without verifying
them against the connected server or current product documentation.

For retrieval agents, use instance-scoped read-only credentials, keep business
actions on separate credentials, and never print or commit a key.

Install `requirements-dev.txt`, then run `python3 scripts/validate_library.py`
and `python3 scripts/scan_secrets.py` after library changes.
