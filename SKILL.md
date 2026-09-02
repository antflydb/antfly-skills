---
name: antfly
description: Provide legacy Antfly guidance for React components, frontend SDKs, A2A, Kubernetes, storage, inference operations, and deployment topics not yet covered by focused Skills. Also use when explicitly asked to explain or list the Antfly Skill catalog; do not use as the default for MCP connection, querying, indexing, connector, troubleshooting, or support-agent tasks.
---

# Antfly Skill Router

Select the smallest focused Skill that covers the task. Do not load the entire
legacy reference tree by default.

## Route by outcome

- MCP connection, credentials, permissions, or smoke tests:
  `skills/foundations/connect-antfly-mcp/SKILL.md`
- Full-text, semantic, hybrid, filtered, graph, or relevance work:
  `skills/foundations/query-antfly/SKILL.md`
- Full-text, embeddings, multimodal, graph, or readiness work:
  `skills/foundations/manage-antfly-indexes/SKILL.md`
- Authentication, ingestion, index, timeout, MCP, or result diagnosis:
  `skills/foundations/troubleshoot-antfly/SKILL.md`
- GitHub ingestion:
  `skills/connectors/sync-github-to-antfly/SKILL.md`
- S3 or Cloudflare R2 ingestion:
  `skills/connectors/sync-s3-to-antfly/SKILL.md`
- Codex, Claude Code, n8n, or Copilot:
  use the matching Skill under `skills/harnesses/`
- Documentation support experience:
  `skills/use-cases/build-antfly-support-agent/SKILL.md`

Read the selected SKILL.md completely, then load only the references it directs
you to. Combine Skills through the applicable manifest in `guides/`.

## Compatibility references

The root `references/backend`, `references/frontend`, and `references/ops`
directories are retained for tasks not yet covered by focused Skills. Treat
their exact commands, endpoint assumptions, tool counts, and authentication
examples as legacy until verified against current Antfly documentation or live
capability discovery.

## Safety

- Prefer read-only, instance-scoped credentials for retrieval agents.
- Discover live MCP capabilities instead of relying on a fixed tool count.
- Stop on authentication and authorization failures.
- Ask before destructive table, index, document, backup, or restore operations.
- Never print or commit credentials.
