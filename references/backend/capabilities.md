# Capabilities — Exact Tool & Action Matrix

## MCP Tools (16)

Available at `{{ANTFLY_API_URL}}/mcp/v1`. `tools/list` hides tools an identity lacks the tier for on *any* table, and the tier is re-checked fail-closed on every call against the `tableName` argument. Discovery filtering is coarser than the per-call check and is not an authorization boundary — the per-call check is.

| Tool | Action | Mutates? | Key args | Tier |
|------|--------|----------|----------|------|
| `describe_mcp_capabilities` | Protocol, transport, session and tool-split guidance | No | — | `none` |
| `describe_query_request` | Compact schema for `query.queryRequest` | No | — | `none` |
| `list_tables` | Enumerate all tables | No | — | `read` (on table `"*"`) |
| `describe_table` | Schema, indexes, ranges, storage status | No | `tableName` | `read` |
| `list_indexes` | List indexes with per-shard status | No | `tableName` | `read` |
| `describe_indexes` | Alias of `list_indexes` — same handler, identical output | No | `tableName` | `read` |
| `get_document` | Fetch one document by key | No | `tableName`, `key`, `fields[]` | `read` |
| `sample_documents` | Bounded document sample over a key range | No | `tableName`, `limit` (1–100, default 5), `from`, `to`, `inclusiveFrom`, `fields[]` | `read` |
| `query` | Full query contract, raw or shorthand | No | `tableName` + **either** `queryRequest` **or** `fullTextSearch`/`fullTextSearchField`/`semanticSearch`/`indexes`/`fields`/`limit`/`orderBy`/`filterPrefix` | `read` |
| `batch` | Insert, delete, and atomically transform documents | **Yes** | `tableName`, `inserts` (map; `writes` = deprecated alias, exclusive), `deletes[]`, `transforms[]`, `syncLevel` | `write` |
| `create_table` | Create table + default full-text index | **Yes** | `tableName`, `numShards` (default 1 standalone / 3 distributed), `key`, `fields` (**JSON-encoded string**, e.g. `"{\"title\":{\"type\":\"text\"}}"`) | `admin` |
| `drop_table` | Delete a table permanently | **Yes (destructive)** | `tableName` | `admin` |
| `create_index` | Add an embeddings index; live embedder probe (503 if unavailable) | **Yes** | `tableName`, `indexName`, `field`/`template`, `dimension`, `embedder`, `summarizer` (the last two **JSON-encoded strings**, e.g. `"embedder": "{\"provider\":\"antfly\"}"`) | `admin` |
| `drop_index` | Remove an index permanently | **Yes (destructive)** | `tableName`, `indexName` | `admin` |
| `backup` | Create table snapshot | No (creates copy) | `tableName`, `backupId`, `location`, `connection` (all required), `format` (`native`\|`portable`, default `portable`) | `admin` |
| `restore` | Restore table from snapshot | **Yes (overwrites)** | `tableName`, `backupId`, `location`, `connection` (all required) | `admin` |

Installed extensions register additional MCP tools dynamically (extension members of kind `mcp_tool`), so the live tool count can exceed 16.

`batch.transforms[]` entries are `{ key, operations[], upsert }`; each operation is `{ op, path, value }` with `op` ∈ `$set`, `$setOnInsert`, `$unset`, `$inc`, `$push`, `$addToSet`, `$min`, `$max`. `syncLevel` ∈ `propose` | `write` | `full_text` | `enrichments` | `full_index`, default `propose`.

## A2A Skills (2)

**Requires starting the server with `--experimental`.** Without the flag the routes are never registered and `/a2a` is **404**. With the flag on and auth enabled, `/a2a` additionally requires `admin`: a non-admin identity gets **403 `forbidden`**, not 404. The agent card is not admin-gated — any caller can fetch it once the flag is on.

JSON-RPC at `{{ANTFLY_API_URL}}/a2a` — that path only. Discovery at `/.well-known/agent-card.json`.

| Skill | Action | Streaming? | Input | Output |
|-------|--------|-----------|-------|--------|
| `query-builder` | Natural language → Antfly `QueryRequest` (LLM optional; with no generator the deterministic builder runs **silently** — no warning) | Yes | Text intent + optional `table`, the only field the adapter forwards (a `context` key is discarded; `constraints`, `example_documents`, `schema_fields`, `session_id`, `mode`, and the rest are REST-only) | One artifact `query`: the whole `QueryBuilderResult` — mandatory `query`, optional `query_request`/`retrieval_query_request`, plus `status`, `steps`, `questions`, `plan`, `explanation`, `confidence`, `warnings` (omitted when empty) |
| `retrieval` | RAG: pipeline by default, agentic when `max_internal_iterations > 0` | Yes | Text query + a data part supplying **`table` or `queries`** (neither → task fails, invalid retrieval agent request); `limit` applies only to the `table`-derived default query; optional `steps`, `max_internal_iterations` | Artifact updates named per event, each payload wrapped as `{event, data}` (`done` → `result`); status `working` at start, then the `done` payload's `status` verbatim — `completed`, `clarification_required`, or `incomplete`. `failed` comes from the adapter's error branch; `in_progress` is never emitted |

Streaming is a whole-agent capability (`capabilities.streaming: true` on the card), not per-skill — both skills stream via `message/stream`.

## Reachable via MCP, Despite Looking REST-Only

These are all available through MCP; do not route users to REST for them.

| Action | MCP route |
|--------|-----------|
| Transforms (`$set`, `$inc`, `$unset`, …) | `batch.transforms[]` |
| Lookup by key | `get_document` (REST equivalent: `GET /db/v1/tables/{t}/documents/{key}`) |
| Aggregations | `query.queryRequest.aggregations` |
| Graph traversal | `query.queryRequest.graph_searches` |
| Hierarchy / tree search | `query.queryRequest.hierarchy` |
| Joins / foreign sources | `query.queryRequest.join`, `query.queryRequest.foreign_sources` |

## Genuinely REST-Only

REST bases on an Antfly node are `/db/v1`, `/auth/v1`, `/ai/v1`, `/ml/v1`, `/extensions/v1`, and
`/ard/v1`, alongside the agent-protocol surfaces (`/mcp/v1`, `/a2a`).

The node API never serves an `/api/v1` base — that path belongs to Colony's platform API, a
different service.

| Action | Endpoint | Why not in MCP |
|--------|----------|---------------|
| Linear merge (bulk import) | `POST /db/v1/tables/{t}/merge` | Cursor-based bulk workflow |
| Transactions | `/db/v1/transactions/*` — sessions (`begin`, `{id}/stage`, `{id}/read`, `{id}/write`, `{id}/delete`, `{id}/savepoints`, `{id}/commit`, `{id}/abort`) plus the stateless OCC `POST /db/v1/transactions/commit`, which requires **both** `read_set` and the `tables` write set in one request | Multi-step stateful protocol; the OCC form needs client-held read versions |
| Cross-table batch | `POST /db/v1/batch` | MCP `batch` is single-table |
| User management | `/auth/v1/users/{userName}` | Auth/admin scope |
| API key management | `/auth/v1/users/{userName}/api-keys` | Auth/admin scope |
| Permissions | `/auth/v1/users/{userName}/permissions` | Auth/admin scope |

## Decision Guide

| Need | Use |
|------|-----|
| Inspect tables, schemas, indexes | MCP (`describe_table`, `describe_indexes`) |
| See what documents look like | MCP (`sample_documents`) |
| Create/drop tables and indexes | MCP (admin identity) |
| Insert, delete, or update documents in place | MCP (`batch`, with `transforms` for updates) |
| Anything from simple search to graph/hierarchy/join | MCP (`query` with `queryRequest`) |
| Bulk import / migration | REST (`POST /db/v1/tables/{t}/merge`) |
| Multi-table atomic writes | REST (`/db/v1/transactions/*` or `POST /db/v1/batch`) |
| RAG with streaming answers | REST `POST /db/v1/agents/retrieval` (stable), or A2A `retrieval` (experimental + admin) |
| Natural language → search query | REST `POST /db/v1/agents/query-builder`, MCP (`describe_query_request` + `query`), or A2A `query-builder` |
| User/permission/API key management | REST (`/auth/v1/...`) |
