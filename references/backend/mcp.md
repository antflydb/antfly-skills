# MCP Server — Model Context Protocol

## What It Is

Antfly has a built-in MCP server that lets AI agents interact with the database directly — create tables, run queries, manage indexes, insert data — all from within the IDE. No SDK needed.

**Endpoint**: `{{ANTFLY_API_URL}}/mcp/v1/`

The MCP server starts automatically with the metadata server. No separate process or configuration needed.

## Setup

### Claude Code

Add to your MCP config (`.claude/settings.json` or project settings):

```json
{
  "mcpServers": {
    "antfly": {
      "type": "url",
      "url": "{{ANTFLY_API_URL}}/mcp/v1/"
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
      "type": "url",
      "url": "{{ANTFLY_API_URL}}/mcp/v1/"
    }
  }
}
```

### Local Development

If running `antfly swarm` locally, the MCP server is at `http://localhost:8080/mcp/v1/`.

## Tools (10)

### Table Management

**`create_table`** — Create a new table
- `tableName` (required) — table name
- `numShards` (default: 3) — number of horizontal partitions
- `key` — key field name
- `fields` — JSON object defining field schema
- Automatically creates a default full-text index

**`drop_table`** — Remove a table
- `tableName` (required)

**`list_tables`** — List all tables with storage, schema, and index info
- No arguments. Returns table metadata including shard counts and index configurations.

### Index Management

**`create_index`** — Create an index on a table
- `tableName` (required)
- `indexName` (required)
- `field` or `template` — what to index (field name or handlebars template)
- `dimension` — vector dimension (auto-detected if embedder configured)
- `embedder` — JSON config for embedding provider (validated on creation)
- `summarizer` — JSON config for summarization
- Validates embedder connectivity by running a test call on creation

**`drop_index`** — Remove an index
- `tableName`, `indexName` (both required)

**`list_indexes`** — List indexes for a table with shard status
- `tableName` (required)
- Returns detailed index configuration and per-shard status

### Data Operations

**`batch`** — Bulk insert and/or delete documents
- `tableName` (required)
- `writes` — map of `doc_id → fields` (JSON objects)
- `deletes` — array of doc IDs to remove
- Automatically partitions across shards and runs in parallel
- Single-insert fast path for individual documents

### Search

**`query`** — Execute search (full-text, semantic, hybrid)
- `tableName` (required)
- `fullTextSearch` — Bleve query string syntax (e.g., `"title:laptop AND price:<2000"`)
- `semanticSearch` — natural language query for vector similarity
- `indexes` — which embedding indexes to search (required for semantic)
- `fields` — fields to return
- `limit` (default: 10)
- `orderBy` — sort configuration
- `filterPrefix` — key prefix filter

### Backup & Restore

**`backup`** — Create a table backup
- `tableName`, `backupID`, `location` (e.g., `file:///path` or S3 URL)

**`restore`** — Restore a table from backup
- `tableName`, `backupID`, `location`
- Validates backup matches table name

## Typical Agent Workflow

1. `list_tables` — see what exists
2. `create_table` with fields — set up the schema
3. `create_index` with embedder config — enable semantic search
4. `batch` with writes — load data
5. `query` with semanticSearch + indexes — search it

## Sharp Edges

1. **MCP endpoint is on the metadata API port** (8080 by default), not the health port (4200)
2. **`create_index` validates embedder on creation** — if the embedding provider is unreachable, creation fails immediately (this is intentional — fail fast)
3. **`query` requires `indexes` for semantic search** — same rule as the REST API, silently returns nothing without it
4. **`batch` partitions across shards** — large writes are parallelized automatically, but errors are grouped by shard
5. **No auth in MCP yet** — the MCP server inherits the metadata server's auth configuration
6. **Streaming** — MCP uses streamable HTTP transport, not SSE. For streaming RAG, use the A2A protocol instead (see [a2a.md](a2a.md))
