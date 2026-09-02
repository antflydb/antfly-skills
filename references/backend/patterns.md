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
7. Add `filter_query` for category/price filters, `aggregations` for facet counts
8. UI: `<Antfly>` → `<QueryBox mode="live">` → `<Facet>` sidebar → `<Results>` with custom cards

**Sharp edges**: Always specify `indexes` in query. Facet a `text` field through its derived `.keyword` subfield rather than the analyzed field. Use `sync_level: "full_index"` if querying right after load.

## Documentation Q&A (RAG)

**Goal**: Users ask questions, get LLM-generated answers with citations from indexed docs.

**Steps**:
1. Create table with `embeddings` index: template `{{heading}} {{content}}`, chunking enabled (`chunker.text.target_tokens: 512`, `chunker.text.overlap_tokens: 50`)
2. Load docs via linear merge (`POST /db/v1/tables/{table}/merge`, cursor pagination on `last_merged_id`)
3. Wait for enrichments: use `sync_level: "enrichments"` (or `"full_index"`) or poll until embeddings are generated
4. Use retrieval agent endpoint with `semantic` + `bm25` strategies
5. Configure `steps.generation` with a generator and system prompt — generation does not run otherwise
6. Stream response: handle `reasoning`, `hit`, `generation`, `followup` SSE events; reconcile against `done`
7. Citations: the default prompt emits inline document ids. For `[resource_id X]` (what the `@antfly/components` parser expects) set `steps.generation.system_prompt` to ask for it
8. UI: `<QueryBox mode="submit">` → `<AnswerResults>` with `showReasoning`, `showFollowUpQuestions`

**Sharp edges**: Chunking config affects answer quality significantly. Too small = fragmented context. Too large = noise. 512 `target_tokens` with 50 `overlap_tokens` is a good starting point; `overlap_tokens` and `separator` only apply to fixed-size chunkers.

## Linear Merge (Sync from an External Source)

**Goal**: Keep an Antfly table in sync with an external sorted source (Postgres, Shopify, a warehouse export).

**Steps**:
1. `POST /db/v1/tables/{table}/merge` with `records` (a map of key → document) and `last_merged_id`
2. First request: `last_merged_id: ""`. Subsequent requests: the `next_cursor` from the previous response
3. The server processes keys in lexicographic order — it sorts the page itself. Your constraint is that **every key in the page is greater than `last_merged_id`**
4. Each page upserts the records it contains and range-deletes Antfly records in that key range that are absent from the page. A record whose content hash matches what Antfly already stores is **skipped**, not rewritten — it lands in the response's `skipped` count, and `upserted` counts only the records that actually changed. A steady-state resync reports `upserted: 0`
5. The server returns status `success` on every accepted page. `partial` and `error` are declared in the spec but the server never emits them — drive the loop off `next_cursor`, not the status
6. Final call: send `records: {}` **with** the last `last_merged_id` to range-delete the tail past the final page

**Sharp edges**: Stateless and idempotent — safe to restart from any page. Not safe for concurrent merges with overlapping key ranges; single-client sync only. Request bodies are capped at 64 MiB (HTTP 413) — the global public-API body cap, not a merge-specific one. `dry_run: true` reports what would be deleted.

## Image / Multimodal Search

**Goal**: Search images by text description or by another image.

**Steps**:
1. Create table with embeddings index using CLIP model
2. Template: `{{media url=image_url}}{{caption}}` — the `{{media url=field}}` helper tells the embedder to process the image
3. Insert documents with `image_url` (URL, data URI, or base64) and optional `caption` text
4. Semantic search with text query: `semantic_search: "sunset over mountains"` + `indexes: ["your_clip_index"]`
5. Results ranked by visual+textual similarity

**Sharp edges**: CLIP models have smaller context than text-only models. Captions help but keep them concise. Remote media fetching is gated: private IPs are blocked by default, there is a download size budget (100 MiB default, lowerable via `remote_content.security.max_download_size_bytes`), and objects in S3 need `remote_content.s3` credentials — which are a separate trust domain from `storage.primary`. Multimodal embeddings are larger (higher dimension) — consider RaBitQ quantization.

## CDC from PostgreSQL

**Goal**: Keep Antfly in sync with a Postgres table, add search capabilities.

**Steps**:
1. PostgreSQL **14+** (replication uses pgoutput protocol v2), rising to **15+** only if you set `publication_filter`, since publication row filters are a 15 feature; `wal_level = logical` (requires restart); and a user with the `REPLICATION` attribute
2. Create the Antfly table with a `replication_sources[]` entry — CDC is declared per table on the table create/update body, not on a separate connection resource
3. Each source: `{type: "postgres", dsn, postgres_table, key_template}`, optionally `slot_name`, `publication_name`, `on_update`, `on_delete`. Use `${secret:...}` in the `dsn`
4. Antfly auto-creates the replication slot and publication (pre-creating them is optional — if you do, set `slot_name` / `publication_name` to point at them)
5. Schema is optional. Default passthrough `$set`s every Postgres column onto the document; `on_update` / `on_delete` override that with explicit transform ops
6. Add embeddings index for semantic search on text columns — replicated writes go through the normal batch path, so enrichments apply as for any write
7. `GET /db/v1/connections?types=cdc` reports replication status (read-only)

**Sharp edges**: `wal_level = logical` is server-wide, affects all databases. Replication slot retains WAL — if Antfly is down for extended time, Postgres disk usage grows. Schema changes in Postgres may require Antfly table updates.

## Multi-Tenant Data

**Goal**: Serve many tenants from one Antfly deployment without leaking documents across them.

**Steps**:
1. Pick an isolation mechanism:
   - **Table-per-tenant** — each tenant gets their own table. Clean isolation, simple auth (one permission per table), at the cost of more tables to manage
   - **Shared table with key prefix** — all tenants share one table, documents keyed as `tenant:{id}:{doc_key}`. Scope queries with `filter_prefix: "tenant:acme:"`. More efficient, but key management is on you
   - **Row filters** — attach a row filter policy to a user or auth subject (role/group) per table
2. Grant permissions to match: per-table for table-per-tenant, per-subject row filters for a shared table
3. For a shared table, make the prefix part of the write path too, so no document can be created outside its tenant's key range

**Sharp edges**: A row filter is enforced server-side on every read, including retrieval-agent scans, aggregations, and graph/tree traversal — it cannot be weakened by the client or by generated tool arguments. `filter_prefix` alone is a client-supplied scope, not enforcement. Start with table-per-tenant for simplicity; move to a shared table when you need to optimize for many (100+) tenants, and back it with row filters when the isolation must be enforced rather than merely requested.
