# Antfly Skills

Primary skill entrypoint: `SKILL.md` — the flagship skill and router into the
focused Skills library (`catalog.yaml`). The reference tree under `references/`
is the CI-verified fact core.

## Agent Protocols

Antfly has built-in MCP and A2A servers:
- **MCP** at `{{ANTFLY_API_URL}}/mcp/v1` — 16 tools for schema discovery, sampling, queries, batch writes, and administration; permission-filtered by the key's scope. See `references/backend/mcp.md`.
- **A2A** at `{{ANTFLY_API_URL}}/a2a` — experimental (`--experimental`; admin permission when auth is enabled); RAG with streaming, query building. The stable RAG surface is `POST /db/v1/agents/retrieval`. See `references/backend/a2a.md`.

## Reference Material
- Start with the focused Skill that covers the task (see `SKILL.md`); fall back to `references/{backend,frontend,ops}/index.md`
- Prefer the current React surface: `AnswerResults`, not `RAGResults`
- Import component styles from `@antfly/components/styles`
- `semantic_search` requires explicit `indexes` — omitting it is rejected with HTTP 422
