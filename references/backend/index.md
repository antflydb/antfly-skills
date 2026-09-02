# Antfly — Backend Skill

## What Antfly Is

Antfly is a distributed database and search engine. It stores JSON documents in tables and provides several index types over them:

- **Full-text (BM25)** — keyword search with relevance scoring
- **Embeddings (vector)** — semantic similarity search using embedding models, dense (HBC — hierarchical balanced clustering) or sparse (SPLADE)
- **Graph** — entity relationships and traversal queries
- **Algebraic** — schema-derived sidecar that accelerates bounded aggregation planning

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
│   └── algebraic — schema-derived aggregation sidecar
└── Enrichments (chunk, asset, embedding artifacts)
    └── On document write, timing is set by sync_level: background
        after the commit at propose/write, but precomputed
        synchronously before the commit at enrichments/full_index,
        where a producer failure rejects the write.
```

**Query flow**: A single query request can combine `full_text_search` + `semantic_search` + `filter_query` + `exclusion_query` + `filter_prefix`. The text and vector result sets are merged per `merge_config` (`rrf` default or `rsf`; the spec's `failover` parses but is rejected with 422). Cross-encoder reranking is optional.

**RAG flow**: the retrieval agent runs multi-strategy search (`semantic`, `bm25`, `metadata`, `tree`, `graph`, `hybrid`) and returns documents. It only generates an answer when `steps.generation` is configured; leave it unset and you get retrieval alone. Separately, `max_internal_iterations` picks the execution mode — `0` (default) is pipeline mode, queries executed directly; `> 0` is agentic mode, where the LLM drives tool calls. With generation on, answers stream over SSE with citations.

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
  Use graph indexes and `graph_searches`
- Tenant isolation in one table:
  Use key prefixes and `filter_prefix`, plus row filters for enforcement

## Agent Protocols (MCP + A2A)

Antfly has built-in MCP and A2A servers — AI agents can interact with the database directly from the IDE.

- **MCP server** at `{{ANTFLY_API_URL}}/mcp/v1` — 16 built-in tools covering table/index management, batch writes, query, backup/restore, and discovery helpers. There is no hierarchy tool: hierarchy is a field of the `query` tool's query request. `tools/list` is filtered per calling identity, so a read-only key sees a read-only server. Read [mcp.md](mcp.md).
- **A2A protocol** at `{{ANTFLY_API_URL}}/a2a` — 2 skills: `retrieval` (RAG with streaming + multi-turn) and `query-builder` (natural language → Antfly query). Requires the server to run with `--experimental`. Read [a2a.md](a2a.md).
- **Agent card** at `{{ANTFLY_API_URL}}/.well-known/agent-card.json` — standard A2A discovery.

Use MCP for database operations. Use A2A for intelligent search and reasoning.

## REST API

Two bases for the database and auth surfaces: `{{ANTFLY_API_URL}}/db/v1` and `{{ANTFLY_API_URL}}/auth/v1` (inference lives under `/ai/v1`). There is no `/api/v1`. OpenAPI spec available. Auth via API key, Bearer, or Basic — all three carry a credential in the `Authorization` header; there is no OAuth flow.

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
| Rust | `pgaf` (`rs/crates/pgaf`) | PostgreSQL extension (pgrx) |

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
- [a2a.md](a2a.md) — A2A protocol: retrieval agent + query builder skills
- [connect.md](connect.md) — auth, client setup, API bases
- [schema.md](schema.md) — tables, JSON Schema, x-antfly-* extensions, field types
- [indexes.md](indexes.md) — full-text, embeddings, graph, algebraic indexes and enrichments
- [data.md](data.md) — insert, upsert, batch, linear merge, transforms, delete, sync levels
- [search.md](search.md) — full-text, vector, hybrid search, filters, facets, reranking, pagination
- [rag.md](rag.md) — retrieval agent, streaming, answer generation, citations
- [integrations.md](integrations.md) — CDC from Postgres, S3, document sync
- [auth.md](auth.md) — users, API keys, RBAC, permissions, row filters
- [capabilities.md](capabilities.md) — exact MCP tool / A2A skill / REST capability matrix with per-tool args and permission tiers
- [patterns.md](patterns.md) — common recipes (hybrid search app, doc Q&A, image search, CDC)

## Critical Sharp Edges

1. `semantic_search` queries **require** an `indexes` entry — omitting it (or sending it empty) is rejected with **HTTP 422** (`unsupported query request`), not empty results. An `indexes` entry naming an index that does not exist is a **500** (`query failed`) instead, because `EmbeddingIndexNotFound` falls through the query error switch — so a 500 on a semantic query means check the index name
2. `x-antfly-types` is an **array** (e.g. `["text", "keyword"]`), not a string
3. API key auth header is `Authorization: ApiKey base64(keyID:keySecret)` — base64 of both ID and secret joined by a colon
4. `sync_level: "full_index"` is what you need to query vector results immediately after writing; `"aknn"` is a removed alias servers reject
5. Sortability requires a `sortable: true` mapping — `x-antfly-field` or `dynamic_templates[].mapping`; `_id` is always sortable. Text fields are never sortable, sort on `field.keyword` instead; anything else is a 422
6. API key secret is returned once at creation — the response also includes a ready-made `encoded` credential, so store that
7. Transforms bypass schema validation — they can produce documents the schema would have rejected
8. The query-string grammar is Antfly's own Lucene-style subset, not Bleve or Elasticsearch parity
