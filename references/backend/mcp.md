# MCP Server — Model Context Protocol

## What It Is

Antfly has a built-in MCP server that lets AI agents interact with the database directly — inspect schemas, run queries, write documents, manage indexes — all from within the IDE. No SDK needed.

**Endpoint**: `{{ANTFLY_API_URL}}/mcp/v1` (canonical, **no trailing slash**)

Also served:

| Path | Purpose |
|------|---------|
| `/mcp/v1` | Main MCP endpoint |
| `/mcp/v1/extensions/{name}` | Single-extension MCP surface |
| `/mcp/v1/extensions/profiles/copilot` | Alias for the main endpoint, for clients configured against a profile path |

The profile path applies no Copilot-specific filtering: it serves the same full built-in tool set as
`/mcp/v1`. Only the literal name `copilot` is routed — any other profile name is **404**.

The MCP server starts automatically with the metadata server. No separate process or configuration needed.

## Transport

Streamable HTTP, protocol version **`2025-06-18`**.

| Method | Behavior |
|--------|----------|
| `POST /mcp/v1` | JSON-RPC requests. `initialize` returns an `Mcp-Session-Id` header |
| `GET /mcp/v1` | Opens the server→client channel as `text/event-stream`; cursor advances via `Last-Event-ID` |
| `DELETE /mcp/v1` | Closes the session |

The `GET` is not a long-lived stream. It answers with a single `event: endpoint` frame naming the
endpoint (carrying an `id:` line when the session store is active) and ends. With a session store
configured, a request with no `Mcp-Session-Id` is **400** and one naming an unknown session is
**404**.

SSE is the *stream encoding* of streamable HTTP — the two are not alternatives. `Last-Event-ID` advances the cursor; there is **no historical replay** of events emitted before the client connected.

## Security Model

When auth is enabled, every MCP request is authorized and every tool is permission-gated. When it is not — the default local dev server, no trusted-principal secret configured — there is no identity to check, the permission gates fail **open**, and MCP is unauthenticated. Treat a default local server as unauthenticated; put a scoped key in front of anything shared.

Each tool declares a permission tier (`none`, `read`, `write`, `admin`), enforced at two points:

1. **Discovery** — `tools/list` filters by whether the identity holds the tier on **any** table (or on table `"*"` for the wildcard tools). This is coarser than the per-call check: a client can see a tool it cannot call on a given table.
2. **Invocation** — the tier is re-checked fail-closed on every `tools/call`, against the effective permission for the `tableName` argument. Discovery filtering is UX and explicitly *not* an authorization boundary; the per-call check is.

`list_tables` is special: it requires `read` on table `"*"`, since it enumerates everything.

## Setup

### Claude Code

```bash
claude mcp add --transport http antfly {{ANTFLY_API_URL}}/mcp/v1 \
  --header "Authorization: Bearer $ANTFLY_API_KEY"
```

Without a `--scope` flag that lands in **local** scope: the server is recorded in `~/.claude.json`,
under the entry for the current project, so it is private to you in this project. `--scope project`
writes the shared `.mcp.json` at the project root instead, and `--scope user` writes a user-wide
entry in `~/.claude.json`. Server *definitions* live in those two files; the settings files gate and
permit servers rather than define them. The equivalent hand-written `.mcp.json` — headers included,
since the CLI form above sets one:

```json
{
  "mcpServers": {
    "antfly": {
      "type": "http",
      "url": "{{ANTFLY_API_URL}}/mcp/v1",
      "headers": {
        "Authorization": "Bearer {{ANTFLY_API_KEY}}"
      }
    }
  }
}
```

### Cursor

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "antfly": {
      "type": "http",
      "url": "{{ANTFLY_API_URL}}/mcp/v1",
      "headers": {
        "Authorization": "Bearer {{ANTFLY_API_KEY}}"
      }
    }
  }
}
```

### Local Development

If running `antfly standalone` locally (`swarm` is the legacy alias for the same runtime), the MCP server is at `http://localhost:8080/mcp/v1`.

## Tools (16)

Grouped by permission tier.

### Tier `none` — always visible

**`describe_mcp_capabilities`** — protocol version, transport, session semantics, the deterministic/write/schema-helper tool split, and query-builder handoff guidance. No arguments.

**`describe_query_request`** — compact guidance for the raw `QueryRequest` accepted by `query.queryRequest`, including the top-level field list and worked examples. No arguments. Use this instead of relying on `tools/list` to inline the full recursive OpenAPI schema.

### Tier `read`

**`list_tables`** — list Antfly tables. No arguments. Requires `read` on table `"*"`.

**`describe_table`** — schema, indexes, ranges, and storage status where available
- `tableName` (required)

**`list_indexes`** / **`describe_indexes`** — index configuration and per-shard status
- `tableName` (required)
- The two names are **aliases**: same handler, same arguments, byte-identical output. Two entries in
  `tools/list`, one behavior

**`get_document`** — fetch one document by key
- `tableName` (required), `key` (required)
- `fields` — array of field names to project

**`sample_documents`** — bounded document sample via the table lookup/scan route
- `tableName` (required)
- `limit` — 1–100, default 5
- `from`, `to` — key range bounds
- `inclusiveFrom` — include the `from` key
- `fields` — array of field names to project

**`query`** — run a table query. See below.

### Tier `write`

**`batch`** — insert, delete, or atomically transform documents
- `tableName` (required)
- `inserts` — map of `doc_id → document object`
- `writes` — **deprecated** alias for `inserts`; mutually exclusive with it
- `deletes` — array of doc IDs
- `transforms` — array of `{ key, operations[], upsert }`, where each operation is `{ op, path, value }` and `op` is one of `$set`, `$setOnInsert`, `$unset`, `$inc`, `$push`, `$addToSet`, `$min`, `$max`. `upsert` is per-key, default `false`
- `syncLevel` — `propose` | `write` | `full_text` | `enrichments` | `full_index`, default `propose`

### Tier `admin`

**`create_table`**
- `tableName` (required)
- `numShards` — topology-aware default: **1** standalone, **3** distributed
- `key` — key field name
- `fields` — the schema, as a **JSON-encoded string**, not an object: the tool schema types it
  `{"type": "string"}` and the server parses it. Pass `"fields": "{\"title\":{\"type\":\"text\"}}"`,
  not `"fields": {...}`. Unparseable content comes back as a tool error, not a schema violation
- Creates a default full-text index

**`drop_table`** — `tableName` (required)

**`create_index`**
- `tableName`, `indexName` (both required)
- `field` or `template` — what to index (field name or handlebars template)
- `dimension` — vector dimension
- `embedder` — embedding provider config as a **JSON-encoded string**, e.g.
  `"embedder": "{\"provider\":\"antfly\",\"model\":\"embed\"}"`
- `summarizer` — summarization config, likewise a JSON-encoded string
- Index `type` is hardcoded to `embeddings`; use REST for other index types
- Runs a **live embedder probe** on creation — if the probe is unavailable the call fails with **503**

**`drop_index`** — `tableName`, `indexName` (both required)

**`backup`**
- `tableName`, `backupId`, `location`, `connection` — **all four required**
- `format` — `native` | `portable`, default `portable`
- `backupId` must match `^[A-Za-z0-9][A-Za-z0-9._-]*$`, max 128 chars

**`restore`**
- `tableName`, `backupId`, `location`, `connection` — **all four required**
- Same `backupId` pattern as `backup`

### Extension tools

Installed extensions register additional MCP tools dynamically — every extension member of kind `mcp_tool` becomes a tool, gated by the extension's declared capabilities and scope. These are on top of the 16 built-ins, so `tools/list` length varies by deployment.

## The `query` Tool

`tableName` is always required. Then choose **one** of two mutually exclusive paths.

### Raw path (primary)

**`queryRequest`** — a raw Antfly `QueryRequest` body, passed straight through to `POST /db/v1/tables/{tableName}/query`. This is the full query contract: `query`, `full_text_search`, `filter_query`, `exclusion_query`, `semantic_search`, `embedding_template`, `indexes`, `embeddings`, `fields`, `hierarchy`, `limit`, `offset`, `order_by`, `search_after`/`search_before`, `filter_prefix`, `aggregations`, `graph_searches`, `join`, `foreign_sources`, `reranker`, `pruner`, `merge_config`, `count`, `profile`, and more.

Call `describe_query_request` first to get the compact schema. Do not set `queryRequest.table` — use `tableName`.

### Shorthand path

Convenience arguments for simple searches:

| Arg | Meaning |
|-----|---------|
| `fullTextSearch` | Bleve-style query string, **or** a full_text_search object |
| `full_text_search` | Snake-case object form, passed through verbatim; takes precedence over `fullTextSearch` |
| `fullTextSearchField` | Turns a `fullTextSearch` string into a match on that field |
| `semanticSearch` | Natural-language query for vector similarity |
| `indexes` | Which embedding indexes to search (required for semantic) |
| `fields` | Fields to return |
| `limit` | Default 10 |
| `orderBy` | Sort configuration |
| `filterPrefix` | Key prefix filter |

Setting `queryRequest` alongside **any** shorthand argument is a schema violation.

## Antfly Cloud

Hosted MCP is served by the Colony cloud gateway:

```
https://platform.antfly.io/cloud/v1/{INSTANCE_ID}/mcp/v1
Authorization: Bearer <cloud API key>
```

`platform.antfly.io` is the production host; dev and staging environments sit on different hosts. The path shape is the same everywhere.

The API key must belong to that instance — a key for a different instance gets **403**. A missing or malformed key gets **401**. `Bearer` is the documented scheme, and the key itself must carry the `antflydb_` prefix; anything else is rejected as "not a cloud API key".

The prefix is what is actually enforced, not the scheme word: the gateway strips a leading `Bearer `
or `ApiKey ` and otherwise takes the header value as-is, so `ApiKey antflydb_...` and a bare
`antflydb_...` are both accepted. Separately, a request that already carries a validated Colony
browser session is authenticated from that session and skips API-key auth entirely.

The gateway authenticates the caller, mints a short-lived (5 minute) trusted-principal token, **strips the client's `Authorization`, `Cookie`, and `X-Antfly-Tenant` headers**, and forwards to the instance's native `/mcp/v1` as `X-Antfly-Trusted-Principal`. `Mcp-Session-Id` passes through in both directions, so sessions work normally.

**A request carrying an `Origin` header is rejected with 403** — `/mcp/v1` is not one of the routes the gateway opens to browsers (only table query routes and `/db/v1/agents/retrieval` are). The check runs in the gateway's browser-admission step, ahead of any MCP handling, so the rejection is not an MCP-level error. The one exception is a request already carrying a validated Colony browser session: that path is admitted as long as it is same-origin. Treat hosted MCP as a server-side surface.

Tool filtering is server-side: the token carries the key's scope, and the instance filters `tools/list` from it.

| Key scope | Tools exposed |
|-----------|---------------|
| read-only | `query`, `get_document`, `describe_table`, `list_indexes`, `describe_indexes`, `sample_documents`, `describe_query_request`, `describe_mcp_capabilities`, plus `list_tables` unless the key is scoped to a table list |
| read-write | the above plus `batch` |
| admin | all 16 built-in tools (plus any extension tools) |

An unscoped key carries no table list, so the instance grants it its operations on table `"*"` and `list_tables` is available; admin keys get `"*"` too. Only a key scoped to specific table names loses `list_tables`, since that tool requires `read` on `"*"`.

## Typical Agent Workflow

**Discovery first** — this is the path the server itself recommends:

1. `describe_mcp_capabilities` — learn the protocol surface and which tools exist
2. `list_tables` → `describe_table` — find the table and its schema/indexes
3. `sample_documents` — see what documents actually look like
4. `describe_query_request` — get the compact QueryRequest schema
5. `query` with `queryRequest` — run the real query

**Creating from scratch** (admin identity):

1. `create_table` with `fields` — set up the schema
2. `create_index` with `embedder` — enable semantic search
3. `batch` with `inserts` — load data
4. `query` with `semanticSearch` + `indexes` — search it

## Sharp Edges

1. **MCP endpoint is on the metadata API port** (8080 by default), not the health port (4200)
2. **No trailing slash** — `/mcp/v1` is canonical; write it that way in client configs
3. **`queryRequest` and shorthand args are mutually exclusive** — mixing them fails schema validation, not silently
4. **`query` requires `indexes` for semantic search** — same rule as the REST API. A semantic query with no resolvable index list is rejected with HTTP **422 `unsupported query request`**, not an empty result
5. **`create_index` probes the embedder live** — an unreachable embedding provider gives you a 503, by design (fail fast). It also only creates `embeddings` indexes
6. **`backup`/`restore` need all four of `tableName`, `backupId`, `location`, `connection`** — `connection` is easy to forget, and `backupId` is pattern-constrained
7. **`writes` is deprecated** — use `inserts` in `batch`; setting both is rejected
8. **`batch` defaults to `syncLevel: propose`** — documents are accepted but not necessarily fully indexed when the call returns. Raise `syncLevel` if you need read-your-writes against an index
9. **Tool visibility follows your identity** — a shorter `tools/list` than expected means fewer permissions, not a broken server
10. **Never expand `_chunks.*` through MCP** — on hierarchical documents, request focused direct matches with explicit `fields` and bounded ancestor projections, or the result exceeds what the client can consume
11. **Tool results are capped server-side** — `mcp.max_tool_result_bytes` (default **96 KiB**, minimum 512 when set, `0` disables the guard) is checked against the encoded `tools/call` result. An over-budget result is not truncated: the whole thing is replaced by a fixed `isError` message telling you to reduce `limit` and `fields` and avoid `_chunks.*`. Bound the query rather than retrying the same call
