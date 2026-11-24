# Antfly — Backend Skill

## What Antfly Is

Antfly is a distributed database and search engine. It stores JSON documents in tables and provides several index types over them:

- **Full-text (BM25)** — keyword search with relevance scoring
- **Embeddings (vector)** — semantic similarity search using embedding models, dense (HBC — hierarchical balanced clustering — or LEANN) or sparse (SPLADE)
- **Graph** — entity relationships and traversal queries
- **Algebraic** — schema-derived sidecar that accelerates bounded aggregation planning
- **Relational** — secondary indexes over typed columns of `storage_mode: "relational"` tables

These can be combined in a single query (hybrid search), fused by Reciprocal Rank Fusion by default. Antfly also has a built-in retrieval agent (retrieval, optionally plus LLM answer generation with streaming).

## How Concepts Connect

```
Table
├── Documents (JSON, keyed by ID)
├── Schema (optional JSON Schema with x-antfly-* extensions)
│   └── compiles to full-text field mappings; a sortable: true
│       mapping (x-antfly-field or dynamic_templates) is what
│       makes a field sortable
├── Indexes
│   ├── full_text — BM25 with a Lucene-style query-string
│   │   grammar (zig/QUERY_STRING.md). Field types from schema.
│   ├── embeddings — vector index. Uses a field or a handlebars
│   │   template against document fields + an embedding model.
│   │   Supports multimodal (images, audio) via {{media url=field}}.
│   │   Chunking is configurable (chunker.text.target_tokens, overlap).
│   ├── graph — edge types on fields, enables traversal
│   ├── algebraic — schema-derived aggregation sidecar
│   └── relational — typed-column indexes (relational tables)
└── Enrichments (chunk, asset, embedding artifacts)
    └── Produced in the background after commit by default.
        commit_requires: direct_enrichments precomputes them
        before the commit (a producer failure rejects the write);
        sync_level only sets how long the write waits. Omitting
        commit_requires at enrichments/full_index keeps the
        legacy precompute behavior during the migration window.
```

**Query flow**: A single query request can combine `full_text_search` + `semantic_search` + `filter_query` + `exclusion_query` + `filter_prefix`. The text and vector result sets are merged per `merge_config` (`rrf` default or `rsf`; the spec's `failover` parses but is rejected with 422). Cross-encoder reranking is optional.

**RAG flow**: the retrieval agent runs multi-strategy search (`semantic`, `bm25`, `metadata`, `tree`, `graph`, `hybrid`) and returns documents. It only generates an answer when `steps.generation` is configured; leave it unset and you get retrieval alone. Separately, `max_internal_iterations` picks the execution mode — `0` (default) is pipeline mode, queries executed directly; `> 0` is agentic mode — an LLM tool loop when `steps.generation` (or a top-level `generator`/`chain`) supplies a generator, otherwise a deterministic planner. With generation on, answers stream over SSE with citations.

## When To Read Which Backend Module

- Need auth, client setup, or API URL:
  Read `connect.md`
- Need to create or change a table:
  Read `schema.md` and `indexes.md`
- Need insert/upsert/import/sync semantics:
  Read `data.md`
- Need query construction or relevance behavior:
  Read `search.md`
- Need answer generation / streaming:
  Read `rag.md`
- Need external data sync:
  Read `integrations.md`
- Need user permissions or API keys:
  Read `auth.md`
- Need the exact tool/action catalog (MCP args, permission tiers):
  Read `capabilities.md`
- Need a recipe for a common use case:
  Read `patterns.md`

## Feature Selection Guide

- Exact keyword matching and filters:
  Use full-text with `keyword` / `numeric` fields
- Sorting or deep cursor pagination:
  Declare the field with `x-antfly-field` and `sortable: true`
- Semantic similarity:
  Use `semantic_search` with explicit `indexes`
- Keyword + semantic ranking:
  Use hybrid search with `merge_config`
- Citation-backed answers:
  Use the retrieval agent / `AnswerResults`
- Relationship traversal:
  Use graph indexes and `graph_queries` (`graph_searches` is deprecated), or Cypher at `/db/v1/graphs/{g}/query`
- Tenant isolation in one table:
  Use key prefixes and `filter_prefix`, plus row filters for enforcement

## Agent Protocols (MCP + A2A)

Antfly has built-in MCP and A2A servers — AI agents can interact with the database directly from the IDE.

- **MCP server** at `{{ANTFLY_API_URL}}/mcp/v1` — 16 built-in tools covering table/index management, batch writes, query, backup/restore, and discovery helpers. There is no hierarchy tool: hierarchy is a field of the `query` tool's query request. `tools/list` is filtered per calling identity, so a read-only key sees a read-only server. Read [mcp.md](mcp.md).
- **A2A protocol** at `{{ANTFLY_API_URL}}/a2a` — 3 skills: `retrieval` (RAG with streaming + multi-turn), `query-builder` (natural language → Antfly query), and `research` (cited research report). Requires the server to run with `--experimental`. Read [a2a.md](a2a.md).
- **Agent card** at `{{ANTFLY_API_URL}}/.well-known/agent-card.json` — standard A2A discovery.

Use MCP for database operations. Use A2A for intelligent search and reasoning.

## REST API

Two bases for the database and auth surfaces: `{{ANTFLY_API_URL}}/db/v1` and `{{ANTFLY_API_URL}}/auth/v1` (inference lives under `/ai/v1`, which returns 403 unless the server config sets `public_inference.enabled`; agent memory under `/memory/v1`). There is no `/api/v1`. OpenAPI spec available. Auth via API key, Bearer, or Basic — all three carry a credential in the `Authorization` header; there is no OAuth flow.

Key endpoints:
- `/db/v1/tables` — list, create (`POST /db/v1/tables/{table}`), drop; schema at `/db/v1/tables/{table}/schema`; indexes at `/db/v1/tables/{table}/indexes`
- `/db/v1/tables/{table}/batch` — insert, delete, transform documents
- `/db/v1/tables/{table}/merge` — linear merge, bulk sorted upsert (best for imports)
- `/db/v1/tables/{table}/documents/{key}` — lookup by key
- `/db/v1/query` — search (full-text, semantic, hybrid, multi-query via NDJSON); also `/db/v1/tables/{table}/query`
- `/db/v1/agents/retrieval` — retrieval / answer agent with streaming (SSE); `/db/v1/agents/query-builder` for NL → query
- `/db/v1/batch` — cross-table atomic batch; `/db/v1/transactions/*` — OCC and stateful transactions
- `/auth/v1/users` — user management, API keys, permissions, row filters

## SDKs

| Language | Package | Notes |
|----------|---------|-------|
| TypeScript | `@antfly/sdk` | Full client, streaming support |
| Go | `github.com/antflydb/antfly/go/pkg/sdk` | Full client, package `sdk` |
| Python | `antfly-sdk` | Full client, imported as `antfly` |
| Rust | `antfly-sdk` (`rs/crates/sdk`) | Async client generated from the spec |
| Rust | `antfly-postgres` (`rs/crates/postgres`) | PostgreSQL extension (pgrx), `CREATE EXTENSION antfly_postgres;` |

## React Components (`@antfly/components`)

Pre-built UI components that connect to an Antfly backend:

| Component | Purpose |
|-----------|---------|
| `<Antfly>` | Root provider — sets URL, table, auth headers |
| `<QueryBox>` | Search input — `mode="live"` (as-you-type) or `mode="submit"` (Q&A) |
| `<Autosuggest>` | Autocomplete dropdown, composable inside QueryBox |
| `<Facet>` | Faceted navigation |
| `<Results>` | Search results display with pagination |
| `<ActiveFilters>` | Shows/removes active facet selections |
| `<AnswerResults>` | Streaming answer agent UI with reasoning, follow-ups, confidence, citations |
| `<AnswerFeedback>` | Thumbs up/down or star ratings on answers |
| `<ChatBar>` | Multi-turn chat surface — renders `<ChatMessages>` and `<ChatInput>` and provides `ChatContext` |
| `<ChatMessages>` / `<ChatInput>` | Exported separately for custom layouts; must live inside a `<ChatBar>` |

Hooks: `useAnswerStream`, `useSearchHistory`, `useCitations`, `useChatStream`, `useAutosuggestContext`, `useAnswerResultsContext`

## Skill Modules

For deeper context on each area, read:
- [mcp.md](mcp.md) — MCP server: 16 built-in tools, permission-filtered per identity
- [a2a.md](a2a.md) — A2A protocol: retrieval, query-builder, and research skills
- [connect.md](connect.md) — auth, client setup, API bases
- [schema.md](schema.md) — tables, JSON Schema, x-antfly-* extensions, field types
- [indexes.md](indexes.md) — full-text, embeddings, graph, algebraic, relational indexes, aliases, and enrichments
- [data.md](data.md) — insert, upsert, batch, linear merge, transforms, delete, sync levels
- [search.md](search.md) — full-text, vector, hybrid search, filters, facets, reranking, pagination
- [rag.md](rag.md) — retrieval agent, streaming, answer generation, citations
- [integrations.md](integrations.md) — CDC from Postgres, S3, document sync
- [auth.md](auth.md) — users, API keys, RBAC, permissions, row filters
- [capabilities.md](capabilities.md) — exact MCP tool / A2A skill / REST capability matrix with per-tool args and permission tiers
- [patterns.md](patterns.md) — common recipes (hybrid search app, doc Q&A, image search, CDC)

## Capabilities Not Yet Covered in Depth

These ship on the v0.3 line but have no reference page here yet. Doc paths are in the upstream
`antflydb/antfly` repo; none of these endpoints is behind `--experimental`.

| Capability | Endpoint(s) | Stability note | Upstream doc |
|------------|-------------|----------------|--------------|
| SQL | `POST /db/v1/sql`, `/db/v1/sql/prepared`, `/db/v1/sql/connections` | HTTP SQL always on; pgwire listener is opt-in and needs auth | `docs/guides/sql-and-psql.mdx` |
| Databases, namespaces, tablespaces | `/db/v1/databases/{db}/namespaces/{ns}/tables/{t}/…`, `/db/v1/tablespaces` | Mirrors the flat `/db/v1/tables` routes under a catalog path | `zig/SYSTEM_CATALOG.md` |
| Relational tables | `/db/v1/tables/{t}/rows/query`, `/rows/mutate`, `/constraints/{status,repair,retry,retire}` | `storage_mode: "relational"` (typed rows, implies `enforce_types`) | `zig/RELATIONAL.md` |
| Lake attachments | Relational table with `base_source` (`kind: external`, Parquet or Iceberg); read via `rows/query` or SQL | Read-only for row writes; Iceberg commits only through an explicit `iceberg_writer` binding (`/db/v1/tables/{t}/lake/*`) | `zig/LAKES.md` |
| Decisions and cascades | `POST /ai/v1/decisions` | Cascades are deciders with `decision_method: cascade` | `docs/reference/decisions.md` |
| Agent memory | `/memory/v1/spaces/…`, MCP at `/memory/v1/mcp`, `/memory/v1/mcp/agent` | Own base and MCP servers | `docs/guides/agent-memory.mdx` |
| Research agent and jobs | `POST /db/v1/agents/research`, `/db/v1/agents/research/jobs/{id}/{advance,cancel}` | Also the A2A `research` skill | `docs/guides/deep-research.mdx` |
| Retrieval navigation and web fetch | `POST /db/v1/agents/retrieval` (`navigate`, `web_search`, `fetch` tools) | Only in the model-directed LLM tool loop | `docs/guides/graph-navigation.mdx` |
| Table privacy | `/db/v1/tables/{t}/privacy`, `/privacy/preview`, `/privacy/scans`, `/privacy/findings` | Policy plus scan/finding workflow | `docs/reference/table-privacy.md` |
| Index aliases | `/db/v1/tables/{t}/index-aliases/{alias}` | See [indexes.md](indexes.md#index-aliases) | `docs/guides/artifact-indexes.mdx` |
| Graph metrics and Cypher | `/db/v1/tables/{t}/indexes/{i}/graph-metrics/{metric}:{action}`, `POST /db/v1/graphs/{g}/query` | Cypher runs against named graphs (`/db/v1/graphs`) | `zig/GRAPH_METRICS.md`, `zig/CYPHER.md` |
| Entity resolvers and curation | `/db/v1/tables/{t}/resolvers/{r}` (`:resolve`, `/redirects`, `/suppressions`, `/reviews`), `/db/v1/tables/{t}/curation/proposals` | Curation proposals settle via `{proposalId}:accept` / `:reject` | `zig/RESOLUTION.md`, `docs/guides/knowledge-graph.mdx` |
| Managed Postgres source | `/db/v1/tables/{t}/sources/managed` | Replace guarded by table ID and source hash | `docs/guides/cdc-replication.mdx` |
| Changefeeds | `/db/v1/changefeeds`, `/{feed_id}/events`, `/ack`, `/renew` | Create requires `Idempotency-Key`; access needs `replicate` (or `admin`) | `zig/CDC.md` |

## Critical Sharp Edges

1. `semantic_search` queries **require** an `indexes` entry — omitting it (or sending it empty) is rejected with **HTTP 422** (`unsupported query request`), not empty results. An `indexes` entry naming an index that does not exist is a **500** (`query failed`) instead, because `EmbeddingIndexNotFound` falls through the query error switch — so a 500 on a semantic query means check the index name
2. `x-antfly-types` is an **array** (e.g. `["text", "keyword"]`), not a string
3. API key auth header is `Authorization: ApiKey base64(keyID:keySecret)` — base64 of both ID and secret joined by a colon
4. `sync_level: "full_index"` is what you need to query vector results immediately after writing; `"aknn"` is a removed alias servers reject
5. Sortability requires a `sortable: true` mapping — `x-antfly-field` or `dynamic_templates[].mapping`; `_id` is always sortable. Text fields are never sortable, sort on `field.keyword` instead; anything else is a 422
6. API key secret is returned once at creation — the response also includes a ready-made `encoded` credential, so store that
7. Transforms bypass schema validation — they can produce documents the schema would have rejected
8. The query-string grammar is Antfly's own Lucene-style subset, not Bleve or Elasticsearch parity
