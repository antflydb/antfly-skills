# Library taxonomy

## Public terminology

- **Guide:** complete, opinionated customer outcome package composed of human-facing instructions, Skills, optional Starters, policies, and executable evaluations. Guides are surfaced in the Antfly UI and documentation.
- **Skill:** agent-executable instructions and resources.
- **Connector:** product integration configured or operated by a Skill.
- **Starter:** optional project code or workflow assets.
- **Template:** an internal reusable asset, not a top-level catalog category.

Reserve **Quickstart** exclusively for the general Antfly installation and
getting-started tutorial. Do not use it for a Guide, Skill, connector, or Starter.

## Skill categories

1. `foundations`: reusable Antfly operations.
2. `connectors`: ingestion-source configuration and verification.
3. `harnesses`: agent-runtime connection, secrets, and tool-boundary behavior.
4. `use-cases`: business outcomes that compose the other categories.
5. `deployments`: environment-specific operations when sufficiently distinct.

Avoid cross-product packages such as `support-agent-codex-github`. Compose the
support-agent, Codex, and GitHub skills through a Guide manifest instead.

## Naming

- Use lowercase hyphen-case and fewer than 64 characters.
- Use verb-led names: `query-antfly`, `sync-github-to-antfly`.
- Put all trigger conditions in SKILL.md `description`.
- Keep SKILL.md concise; route detailed or variable material into `references/`.

## Lifecycle

`experimental` → `preview` → `verified` → `deprecated`

A verified Guide must declare compatible Antfly/MCP versions and pass structure,
security, live-contract, retrieval, citation, failure, and harness smoke tests.
