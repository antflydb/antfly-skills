# Antfly — Backend Skill

## What Antfly Is

Antfly is a distributed database and search engine. It stores JSON documents in tables and provides three types of indexes over them:

- **Full-text (BM25)** — traditional keyword search with relevance scoring
- **Embeddings (vector)** — semantic similarity search using embedding models
- **Graph** — entity relationships and traversal queries

These can be combined in a single query (hybrid search) using Reciprocal Rank Fusion (RRF). Antfly also has a built-in RAG pipeline (retrieval + LLM answer generation with streaming).

## How Concepts Connect

```
Table
├── Documents (JSON, keyed by ID)
├── Schema (optional JSON Schema with x-antfly-* extensions)
│   └── automatically maps to full-text index field mappings
├── Indexes
│   ├── full_text — BM25, powered by Bleve. Field types from schema.
│   ├── embeddings — vector index. Uses a handlebars template
│   │   against document fields + an embedding model. Supports
│   │   multimodal (images, audio) via {{media url=field}} helper.
│   │   Chunking is configurable (target tokens, overlap).
│   └── graph — defines edge types on fields, enables traversal
└── Enrichments (async pipeline)
    └── On document write: auto-generate embeddings, summaries,
        graph edges in background. Controlled by sync_level.
```

**Query flow**: A single query request can combine `full_text_search` (Bleve query) + `semantic_search` (text → embedding → vector similarity) + `filter_query` + `exclusion_query`. Results are merged via RRF. Reranking (cross-encoder) is optional.

**RAG flow**: Retrieval agent runs multi-strategy search (semantic, bm25, graph, hybrid) → retrieves docs → LLM generates answer with citations → streams via SSE.

## API

REST API at `{{ANTFLY_API_URL}}/api/v1`. OpenAPI spec available. Auth via API keys, OAuth, Bearer tokens, or Basic auth.

Key endpoint groups:
- `/tables` — CRUD tables, schema, indexes
- `/{table}/batch` — insert, delete, transform documents
- `/{table}/linear-merge` — bulk sorted upsert (best for imports)
- `/{table}/keys/{key}` — lookup by key
- `/query` — search (full-text, semantic, hybrid, multi-query via NDJSON)
- `/retrieval-agent` — RAG with streaming (SSE)
- `/transaction` — multi-table atomic batch
- `/users` — user management, API keys, permissions

## SDKs

| Language | Package | Notes |
|----------|---------|-------|
| TypeScript | `@antfly/sdk` | Full client, streaming support |
| Go | `github.com/antflydb/antfly/pkg/client` | Full client |
| Python | `antfly` | Full client |
| Rust | `pgaf` | PostgreSQL extension |

## React Components (`@antfly/components`)

Pre-built UI components that connect to an Antfly backend:

| Component | Purpose |
|-----------|---------|
| `<Antfly>` | Root provider — sets URL, table, auth headers |
| `<QueryBox>` | Search input — `mode="live"` (as-you-type) or `mode="submit"` (Q&A) |
| `<Autosuggest>` | Autocomplete dropdown, composable inside QueryBox |
| `<Facet>` | Faceted navigation on keyword fields |
| `<Results>` | Search results display with pagination |
| `<ActiveFilters>` | Shows/removes active facet selections |
| `<RAGResults>` | RAG answer with streaming, citation support |
| `<AnswerResults>` | Answer agent Q&A with reasoning, follow-ups, confidence |
| `<AnswerFeedback>` | Thumbs up/down or star ratings on answers |

Hooks: `useAnswerStream`, `useSearchHistory`, `useCitations`

## Skill Modules

For deeper context on each area, read:
- [connect.md](connect.md) — auth, client setup, API URL
- [schema.md](schema.md) — tables, JSON Schema, x-antfly-* extensions, field types
- [indexes.md](indexes.md) — full-text, embeddings, graph indexes and enrichments
- [data.md](data.md) — insert, upsert, batch, linear merge, transforms, delete, sync levels
- [search.md](search.md) — full-text, vector, hybrid search, filters, facets, reranking, pagination
- [rag.md](rag.md) — retrieval agent, streaming, answer generation, citations
- [integrations.md](integrations.md) — CDC from Postgres, S3, document sync
- [auth.md](auth.md) — users, API keys, RBAC, permissions
- [patterns.md](patterns.md) — common recipes (hybrid search app, doc Q&A, image search, CDC)

## Critical Sharp Edges

1. `semantic_search` queries **require** `indexes: ["index_name"]` — omitting this silently returns zero results
2. `x-antfly-types` is an **array** (e.g., `["text", "keyword"]`), not a string
3. API key auth header format: `Authorization: ApiKey base64(keyID:keySecret)` — the value is base64 of both ID and secret joined by colon
4. `sync_level: "aknn"` is required if you need to query vector results immediately after writing — default `propose` is fast but doesn't wait for vector index
5. Facets only work on `keyword` typed fields, not `text` fields
6. API key secret is only returned once at creation time — must be stored immediately
7. Handlebars templates in embedding indexes must reference fields that actually exist in the document
