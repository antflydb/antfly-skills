# Library roadmap

## Preview release

- Publish the Antfly Documentation Support Agent Guide and 11 initial Skills.
- Verify Codex, Claude Code, n8n, and Copilot with read-only Cloud credentials.
- Replace provisional Antfly compatibility text after the next stable release.
- Require the Guide/Skill validation workflow on pull requests.

## Contract automation

- Compare required and denied tools with `describe_mcp_capabilities`.
- Validate canonical query patterns through `describe_query_request`.
- Run known-positive semantic and hybrid retrieval fixtures.
- Confirm read-only keys hide all mutation and administration tools.
- Track cold connection, warm retrieval, fallback, and complete-answer latency.

## Catalog expansion

- Add OpenAI Agents SDK and Google ADK harness Skills.
- Add website and PostgreSQL connector Skills.
- Add Guides for documentation search, retrieval assessment, agent memory,
  marketing operations, and GEO intelligence.

## Antfly UI

- Render `guide.yaml` as the Guide catalog.
- Ask the user to select a source connector and agent harness.
- Provision or select an appropriately scoped key.
- Generate install instructions or a downloadable Skill bundle.
- Run verification and show completion state inside the Guide.
