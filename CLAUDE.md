# Antfly Skills

Primary skill entrypoint: `SKILL.md`.

## Agent Protocols

Antfly has built-in MCP and A2A servers:
- **MCP** at `{{ANTFLY_API_URL}}/mcp/v1/` — create tables, indexes, insert data, query. See `references/backend/mcp.md`.
- **A2A** at `{{ANTFLY_API_URL}}/a2a` — RAG with streaming, query building. See `references/backend/a2a.md`.

## Reference Material
- Start with `references/backend/index.md` for backend work
- Start with `references/frontend/index.md` for frontend work
- Start with `references/ops/index.md` for ops work
- Prefer the current React surface: `AnswerResults`, not `RAGResults`
- Import component styles from `@antfly/components/styles`
- `semantic_search` requires explicit `indexes`
