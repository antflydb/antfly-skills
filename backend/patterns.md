# Patterns — Common Recipes

Dense recipes for common use cases. Not runnable code — the pattern the AI should follow.

## Hybrid Search App (e.g., Product Catalog)

**Goal**: Users search products with keywords + semantic understanding, filter by category/price, see faceted results.

**Steps**:
1. Create table with both `full_text` and `embeddings` indexes
2. Define schema: `x-antfly-types: ["text", "keyword"]` on name (searchable + facetable), `["keyword"]` on category (facetable), `["numeric"]` on price
3. Set `x-antfly-include-in-all` for fields that should match unscoped queries
4. Embeddings index: template `{{name}} {{description}}`, provider of choice
5. Batch insert products
6. Query: combine `full_text_search` + `semantic_search` + `indexes: ["your_embedding_index"]`
7. Add `filter_query` for category/price filters, facets on keyword fields
8. UI: `<Antfly>` → `<QueryBox mode="live">` → `<Facet>` sidebar → `<Results>` with custom cards

**Sharp edges**: Always specify `indexes` in query. Facets need `keyword` type. Use `sync_level: "aknn"` if querying right after load.

## Documentation Q&A (RAG)

**Goal**: Users ask questions, get LLM-generated answers with citations from indexed docs.

**Steps**:
1. Create table with `embeddings` index: template `{{heading}} {{content}}`, chunking enabled (512 tokens, 50 overlap)
2. Load docs via linear merge (sorted by key, cursor pagination, final orphan cleanup)
3. Wait for enrichments: use `sync_level: "aknn"` or poll until embeddings are generated
4. Use retrieval agent endpoint with `semantic` + `bm25` strategies
5. Configure generator (ollama/openai/anthropic) with system prompt
6. Stream response: handle `reasoning`, `hit`, `generation`, `followup` SSE events
7. Parse `[resource_id X]` citations to link answers to source docs
8. UI: `<QueryBox mode="submit">` → `<AnswerResults>` with `showReasoning`, `showFollowUpQuestions`

**Sharp edges**: Chunking config affects answer quality significantly. Too small = fragmented context. Too large = noise. 512 tokens with 50 overlap is a good starting point.

## Image / Multimodal Search

**Goal**: Search images by text description or by another image.

**Steps**:
1. Create table with embeddings index using CLIP model
2. Template: `{{media url=image_url}}{{caption}}` — the `{{media url=field}}` helper tells the embedder to process the image
3. Insert documents with `image_url` (URL or base64) and optional `caption` text
4. Semantic search with text query: `semantic_search: "sunset over mountains"` + `indexes: ["your_clip_index"]`
5. Results ranked by visual+textual similarity

**Sharp edges**: CLIP models have smaller context than text-only models. Captions help but keep them concise. Image URLs must be accessible from the Antfly server. Multimodal embeddings are larger (higher dimension) — consider RaBitQ quantization.

## CDC from PostgreSQL

**Goal**: Keep Antfly in sync with a Postgres table, add search capabilities.

**Steps**:
1. Enable `wal_level = logical` in PostgreSQL (requires restart)
2. Create a publication on the source table
3. Create Antfly table with schema matching Postgres columns
4. Add embeddings index for semantic search on text columns
5. Configure CDC connection (Postgres host, publication, replication slot)
6. Antfly subscribes to WAL and auto-syncs inserts/updates/deletes
7. Enrichments auto-generate embeddings on replicated data

**Sharp edges**: `wal_level = logical` is server-wide, affects all databases. Replication slot retains WAL — if Antfly is down for extended time, Postgres disk usage grows. Schema changes in Postgres may require Antfly table updates.

## Multi-Tenant Data

Two approaches:

**Table-per-tenant**: Each tenant gets their own table. Clean isolation. Simple auth (permission per table). Overhead: more tables to manage.

**Shared table with key prefix**: All tenants share one table. Documents keyed as `tenant:{id}:{doc_key}`. Use `filter_prefix: "tenant:acme:"` in queries to scope to one tenant. More efficient but requires careful key management.

**Recommendation**: Start with table-per-tenant for simplicity. Move to shared table when you need to optimize for many (100+) tenants.
