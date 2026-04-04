# Capabilities — Exact Tool & Action Matrix

## MCP Tools (10)

Available at `{{ANTFLY_API_URL}}/mcp/v1/`

| Tool | Action | Mutates? | Key args |
|------|--------|----------|----------|
| `list_tables` | Enumerate all tables with metadata | No | — |
| `create_table` | Create table + default full-text index | **Yes** | `tableName`, `numShards`, `fields` |
| `drop_table` | Delete a table permanently | **Yes (destructive)** | `tableName` |
| `list_indexes` | List indexes with per-shard status | No | `tableName` |
| `create_index` | Add index, validates embedder (blocks ≤30s) | **Yes** | `tableName`, `indexName`, `field`/`template`, `embedder` JSON |
| `drop_index` | Remove an index permanently | **Yes (destructive)** | `tableName`, `indexName` |
| `query` | Search: full-text, semantic, hybrid | No | `tableName`, `fullTextSearch`, `semanticSearch`, `indexes`, `fields`, `limit` |
| `batch` | Insert and/or delete documents | **Yes** | `tableName`, `writes` (map), `deletes` (array) |
| `backup` | Create table snapshot | No (creates copy) | `tableName`, `backupID`, `location` |
| `restore` | Restore table from snapshot | **Yes (overwrites)** | `tableName`, `backupID`, `location` |

## A2A Skills (2)

Available at `{{ANTFLY_API_URL}}/a2a` (JSON-RPC). Discovery at `/.well-known/agent.json`.

| Skill | Action | Streaming? | Input | Output |
|-------|--------|-----------|-------|--------|
| `retrieval` | RAG: multi-strategy search + LLM answer generation | Yes | Text query, optional table/config | Hits, answer text, citations, follow-ups |
| `query-builder` | Natural language → structured Bleve query | No | Text intent, optional schema fields | Bleve query JSON, explanation, confidence |

## REST API — Actions NOT Available via MCP

These require the REST API (`{{ANTFLY_API_URL}}/api/v1`):

| Action | Endpoint | Why not in MCP |
|--------|----------|---------------|
| Linear merge (bulk import) | `POST /{table}/linear-merge` | Complex cursor-based workflow |
| Transforms (`$set`, `$inc`, etc.) | `POST /{table}/batch` | MCP batch only supports insert/delete |
| Lookup by key | `GET /{table}/keys/{key}` | Simple GET, use REST directly |
| Transactions | `POST /transaction` | Multi-table atomic operations |
| User management | `POST /users/{name}` | Auth/admin scope |
| API key management | `POST /users/{name}/api-keys` | Auth/admin scope |
| Permissions | `POST /users/{name}/permissions` | Auth/admin scope |
| Aggregations config | via `/query` body | MCP query supports basic search; complex aggregation configs go through REST |
| Graph traversal | via `/query` body | Graph searches use REST query format |
| Tree search | via `/query` body | Hierarchical traversal via REST |
| Joins | via `/query` body | Cross-table joins via REST |

## Decision Guide

| Need | Use |
|------|-----|
| Create/inspect/drop tables and indexes | MCP |
| Insert or delete documents | MCP (`batch`) |
| Simple to hybrid search | MCP (`query`) |
| Bulk import / migration | REST (`linear-merge`) |
| In-place document updates | REST (`batch` with transforms) |
| RAG with streaming answers | A2A (`retrieval` skill) or REST (`/agents/retrieval`) |
| Natural language → search query | A2A (`query-builder` skill) |
| User/permission/API key management | REST |
| Multi-table transactions | REST |
| Graph traversal queries | REST |
