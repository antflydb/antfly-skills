---
name: antfly
description: Use this skill when working with Antfly applications, APIs, schemas, indexes, queries, retrieval-agent flows, React components, or Antfly deployment and operations. It helps choose the right Antfly feature, avoid stale component names and query shapes, and load the smallest useful backend, frontend, or ops context before coding.
---

# Antfly

Use this skill for any task that builds on, debugs, integrates with, or operates Antfly.

## Agent Protocols

Antfly has built-in MCP and A2A servers. AI agents can interact with the database directly:

- **MCP server** at `{{ANTFLY_API_URL}}/mcp/v1` — 16 tools covering schema discovery, document sampling, queries, batch writes, and table/index administration. With auth enabled, tools are permission-filtered by the key's scope (a read-only key gets a read-only surface). See `references/backend/mcp.md`.
- **A2A protocol** at `{{ANTFLY_API_URL}}/a2a` — experimental; requires the server to run with `--experimental`, and with auth enabled `/a2a` additionally requires admin permission. Skills: `retrieval` (RAG with streaming) and `query-builder` (natural language → Antfly QueryRequest). See `references/backend/a2a.md`.

Use MCP for database work. For RAG and answer generation, the stable surface is `POST /db/v1/agents/retrieval` (see `references/backend/rag.md`); A2A offers the same skills on experimental deployments.

## Focused Skills

When a focused Skill covers the task, prefer it over this root skill — install
with `npx skills add antflydb/antfly-skills --full-depth --skill <name>`.
Route by outcome:

- MCP connection, credentials, permissions, or smoke tests:
  `skills/foundations/connect-antfly-mcp/SKILL.md`
- Full-text, semantic, hybrid, filtered, graph, or relevance work:
  `skills/foundations/query-antfly/SKILL.md`
- Full-text, embeddings, multimodal, graph, or readiness work:
  `skills/foundations/manage-antfly-indexes/SKILL.md`
- Authentication, ingestion, index, timeout, MCP, or result diagnosis:
  `skills/foundations/troubleshoot-antfly/SKILL.md`
- GitHub ingestion: `skills/connectors/sync-github-to-antfly/SKILL.md`
- S3 or Cloudflare R2 ingestion: `skills/connectors/sync-s3-to-antfly/SKILL.md`
- Google ADK, Vertex AI, or Google agent deployment with Antfly:
  `skills/harnesses/configure-antfly-google-adk/SKILL.md`
- Codex, Claude Code, n8n, or Copilot:
  use the matching Skill under `skills/harnesses/`
- Documentation support experience:
  `skills/use-cases/build-antfly-support-agent/SKILL.md`
- Google Workspace ingestion and a general agent over Drive, Gmail, Meet or Calendar:
  `skills/use-cases/build-antfly-workspace-agent/SKILL.md`

Read the selected SKILL.md completely, then load only the references it directs
you to. Complete outcome compositions live in `guides/` as playbooks — they are
read, not installed. The reference tree under `references/` is the shared,
CI-verified fact core; focused Skills and this router both draw on it.

## Safety

- Prefer read-only, instance-scoped credentials for retrieval agents.
- Discover live MCP capabilities with `describe_mcp_capabilities` rather than
  relying on a fixed tool count.
- Stop on authentication and authorization failures.
- Ask before destructive table, index, document, backup, or restore operations.
- Never print or commit credentials.

## Reference Material

Start with the smallest useful context:
- Backend task:
  Read `references/backend/index.md`, then only the specific module needed
- Frontend task:
  Read `references/frontend/index.md`, then only the specific module needed
- Ops task:
  Read `references/ops/index.md`, then only the specific module needed
- Full-stack task:
  Read `references/backend/index.md` first, then `references/frontend/index.md`

Before writing code, identify:
- which table(s) are involved
- whether the task is full-text, semantic, hybrid, graph, or retrieval-agent based
- which fields need `x-antfly-field` declarations for sorting, and which embeddings index name is required for semantic search
- whether the environment is `antfly standalone`, distributed / Kubernetes, or serverless

## Backend Routing

For direct agent interaction, prefer MCP tools (see `references/backend/mcp.md`).
For RAG and intelligent search, use the retrieval agent (see `references/backend/rag.md`).
For SDK/API reference, read:
- `references/backend/connect.md` for auth, clients, API URL
- `references/backend/schema.md` for tables, JSON Schema, `x-antfly-*`
- `references/backend/indexes.md` for full-text, embeddings, graph indexes
- `references/backend/data.md` for inserts, batch, linear merge, sync levels
- `references/backend/search.md` for query shapes and search behavior
- `references/backend/rag.md` for retrieval agent and streaming answer flows
- `references/backend/integrations.md` for CDC and document sync
- `references/backend/auth.md` for users, API keys, RBAC
- `references/backend/patterns.md` for common recipes
- `references/backend/capabilities.md` for the exact MCP/A2A/REST capability matrix

Choose features this way:
- exact match / filtering / sorting:
  full-text with the right field declarations (`x-antfly-field` with `sortable: true` for sort fields)
- semantic similarity:
  `semantic_search` with explicit `indexes`
- keyword + semantic relevance:
  hybrid search (RRF by default; `merge_config` selects `rsf` or per-index weights — the spec's `failover` value is rejected at runtime)
- citation-backed answers:
  retrieval agent
- relationship traversal:
  graph indexes and graph queries

## Frontend Routing

Read:
- `references/frontend/sdk.md` for direct SDK use
- `references/frontend/components.md` for React component props and wiring
- `references/frontend/hooks.md` for custom streaming and citation handling
- `references/frontend/patterns.md` for app-level UI recipes

Choose UI this way:
- search page:
  `Antfly` + `QueryBox` + `Facet` + `ActiveFilters` + `Results`
- streaming answer UI:
  `QueryBox mode="submit"` + `AnswerResults`
- custom UI:
  `@antfly/sdk` + `useAnswerStream`

Current React surface:
- use `AnswerResults`, not `RAGResults`
- import styles from `@antfly/components/styles`

## Ops Routing

Read:
- `references/ops/standalone.md` for local single-node setup
- `references/ops/kubernetes.md` for production deployment
- `references/ops/docker.md` for Docker / compose
- `references/ops/storage.md` for storage backends
- `references/ops/secrets.md` for credentials and the secret store
- `references/ops/inference.md` for model serving and inference
- `references/ops/monitoring.md` for health and metrics
- `references/ops/config.md` for exact config keys and env vars

Defaults:
- local dev / quickstart:
  assume `antfly standalone`
- production / HA / autoscaling:
  assume Kubernetes operator and distributed mode

## Critical Antfly Sharp Edges

- `semantic_search` requires `indexes: ["index_name"]` — omitting it is rejected with HTTP 422 ("unsupported query request")
- `x-antfly-types` is an array, not a string
- sortable fields need `sortable: true` via `x-antfly-field` or a dynamic template (`_id` is always sortable); analyzed `text` fields sort via `field.keyword`
- use `sync_level: "full_index"` if vector results must be queryable immediately after writes
- API key auth is `Authorization: ApiKey base64(keyID:keySecret)`
- retrieval agent endpoint is `/db/v1/agents/retrieval`; answer generation runs only when `steps.generation` is configured
- current React package exports `AnswerResults`, not `RAGResults`
- MCP server at `/mcp/v1` — with auth enabled, tools are permission-filtered by the key's scope
- A2A at `/a2a` requires `--experimental` (plus admin permission when auth is enabled); agent card at `/.well-known/agent-card.json`
