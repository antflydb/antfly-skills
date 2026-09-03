# Search — Full-Text, Vector, Hybrid Queries

## Query Endpoints

`POST /db/v1/query` — global query; `table` is a required body field naming the single table the request dispatches to. It is not a cross-table fan-out: every NDJSON line is parsed for its own `table`, and on that NDJSON path a missing or empty one is a **400** (`invalid query request`). With a single JSON body the handler defaults an absent `table` to the empty string and dispatches it, so the answer is a **404** (`not found`) instead.
`POST /db/v1/tables/{tableName}/query` — same request body, table fixed by the path.

Both accept `application/json` (one query) or `application/x-ndjson` (many). Both return the same envelope:

```json
{ "responses": [ { "hits": { ... }, "took": 12, "status": 200 } ] }
```

A `QueryResult` carries `hits`, `aggregations`, `analyses`, `graph_results`, `profile`, `took`, `status`, `error`, and `table`. Joined data arrives inside the hits, not as a separate result object.

## Canonical `query` Field

`query` — the canonical public query AST, and the field to prefer for new clients. Its boolean clauses are normalized before planning:

- `bool.must` is scoring query input — it becomes the full-text query
- `bool.filter` is **non-scoring** query input — it becomes `filter_query`
- `bool.must_not` is non-scoring exclusion — it becomes `exclusion_query`

```json
{ "query": { "bool": {
  "must": [{ "match": { "field": "body", "text": "computer" } }],
  "filter": [{ "term": { "path": "/tenant", "value": "acme" } }],
  "must_not": [{ "exists": { "path": "/deleted_at" } }]
} } }
```

Filter branches accept the same query variants as `filter_query` and `exclusion_query`; structured clauses use the native document-value path, text clauses resolve through the text index before scoring. This is the **only** place a `filter` clause is non-scoring — see the note under Boolean Combinations.

## Full-Text Search (BM25)

`full_text_search` — Antfly's own query DSL.

### Query Types

| Query | Shape |
|-------|-------|
| Match | `{"match": "laptop", "field": "title"}` |
| Term | `{"term": "electronics", "field": "category"}` |
| Multi-match | `{"multi_match": {"query": "lap", "fields": ["title", "body"], "type": "bool_prefix"}}` |
| Match phrase | `{"match_phrase": "high performance", "field": "desc"}` |
| Phrase | `{"terms": ["high", "performance"], "field": "desc"}` |
| Fuzzy | `{"fuzzy": "latop", "field": "title"}` or `{"term": "latop", "fuzziness": "auto", "field": "title"}` |
| Prefix | `{"prefix": "electr", "field": "category"}` |
| Wildcard | `{"wildcard": "lap*", "field": "title"}` |
| Regexp | `{"regexp": "lap.*", "field": "title"}` |
| Numeric range | `{"min": 100, "max": 500, "field": "price", "inclusive_min": true}` |
| Term range | `{"min": "alpha", "max": "omega", "field": "title"}` |
| Date range | `{"start": "2026-01-01T00:00:00Z", "end": "2026-06-01T00:00:00Z", "field": "created"}` |
| Geo distance | `{"location": [-122.4, 37.7], "distance": "5km", "field": "location"}` |
| Geo bbox | `{"field": "loc", "min_lat": 37.7, "min_lon": -122.5, "max_lat": 37.8, "max_lon": -122.3}` |
| Doc ID | `{"ids": ["doc-1", "doc-2"]}` |
| Match all | `{"match_all": {}}` |

Ranges and bounding boxes are **flat** inside `full_text_search` — the bounds sit beside `field`, not nested under a `numeric_range` / `date_range` / `geo_bbox` key. (Structured `filter_query` and `exclusion_query` also accept wrapped forms: `numeric_range`, `term_range`, `date_range`, `range`, `geo_bbox`, `geo_distance`, `geo_shape`, `ip_range`, `bool_field`, `doc_id`, `exists`, `terms`, and `ref` — a named binding declared under `with`. In the wrapped `geo_bbox`, `min_lon > max_lon` deliberately means a box crossing the antimeridian.) `geo_distance` takes `location` as a `[lon, lat]` pair; there are no `lat`/`lon` keys.

Fuzzy has **two accepted wire roots**:
- a `fuzzy` root — `{"fuzzy": "latop", "field": "title"}`, or the object form `{"fuzzy": {"field": "title", "term": "latop", "max_edits": 1, "prefix_length": 0}}` (`query`/`value` are accepted in place of `term`; `max_edits` defaults to 1 and caps at 2)
- a `term` carrying `fuzziness` (integer 0–2, or `"auto"`) and optionally `prefix_length`

Every query accepts `boost`.

### Boolean Combinations

- **AND**: `{"conjuncts": [q1, q2]}`
- **OR**: `{"disjuncts": [q1, q2], "min": 1}`
- **Bool**: `{"bool": {"must": [...], "should": [...], "must_not": [...], "filter": [...]}}` — `must`/`should` score, `must_not` does not.

Inside `full_text_search`, `filter` clauses are folded into `must`, so they **do** score. A non-scoring filter belongs in the top-level `query` field (where `bool.filter` becomes `filter_query`), or in `filter_query` itself; the one exception in `full_text_search` is the shape `{"bool": {"filter": [...], "boost": 0}}`, whose zero boost removes the contribution.

### String Query Shorthand

`{"query": "title:laptop AND price:[* TO 2000}"}` — the query-string grammar. Default field `_all`, default operator `AND`. The wire shape is `{query, boost}` only — there is no `default_operator` field to override it. Supports field-scoped terms, phrases with `~slop`, `+`/`-`/`AND`/`OR`/`NOT`, field groups `title:(a OR b)`, prefix `pre*`, field-scoped regex `title:/foo.*/`, field-scoped fuzzy `title:~term`, boosts `^2`, and inline ranges `age:[10 TO 20}`.

## Semantic Search (Vector)

`semantic_search` — pass a text string; Antfly embeds it and finds similar documents.

**Required**: `indexes`, naming the embeddings index or indexes to search.

```json
{
  "table": "products",
  "semantic_search": "comfortable office chair for long hours",
  "indexes": ["product_embeddings"],
  "limit": 20
}
```

Use `embedding_template` for multimodal query embedding (`{{remoteMedia url=this}}`).

Distance filters (lower distance = more similar):
- `distance_under` — maximum distance; drops far, low-confidence matches
- `distance_over` — **minimum** distance; drops the *most similar* hits. Use it for dedupe and dissimilarity searches, not for quality filtering

## Hybrid Search

Combine `full_text_search` + `semantic_search` in one query; results are fused.

```json
{
  "table": "products",
  "full_text_search": { "query": "ergonomic chair" },
  "semantic_search": "comfortable seating for office work",
  "indexes": ["product_embeddings"],
  "merge_config": {
    "strategy": "rrf",
    "rank_constant": 60,
    "weights": { "full_text": 0.3, "product_embeddings": 1.0 }
  },
  "limit": 15
}
```

`merge_config.strategy`:
| Strategy | Behavior |
|----------|----------|
| `rrf` (default) | Reciprocal Rank Fusion, `1/(rank_constant + rank)`; `rank_constant` defaults to 60 |
| `rsf` | Relative Score Fusion — min/max normalize within `window_size` (defaults to `limit`), then combine |

`rrf` and `rsf` are the only strategies that execute. `failover` is in the spec enum, so it parses, but the request contract rejects it before planning with **HTTP 422** (`unsupported query request`) — there is no failover behavior to fall back on.

`weights` is keyed by index name, with `full_text` as the key for the text side. Unspecified indexes default to 1.0; weights apply to both RRF and RSF.

## Filters

**filter_query** — must match, does not contribute to relevance:
```json
{ "filter_query": { "term": "electronics", "field": "category" } }
```

**exclusion_query** — must not match:
```json
{ "exclusion_query": { "term": "discontinued", "field": "status" } }
```

**filter_prefix** — filter by key prefix (multi-tenant or hierarchical data):
```json
{ "filter_prefix": "tenant:acme:" }
```

All three are applied **before** scoring, not as a post-filter on the result page — they shrink the candidate set rather than trimming results after ranking. Filters use the same query shapes as `full_text_search`.

## Aggregations / Facets

Facet-style counts come from `aggregations`:

```json
{
  "aggregations": {
    "categories": { "type": "terms", "field": "category", "size": 10 }
  }
}
```

Results come back under `aggregations.<name>.buckets` with `key` and `doc_count`. Terms aggregations extract the value from the stored document JSON by path, so they are **mapping-independent** — a field does not need a `keyword` mapping to be faceted, and nested paths work. `fields` (instead of `field`) produces multi-field composite buckets, whose `key` is a JSON **string** carrying a serialized array (`"[\"alice\",\"book\"]"`) — `key` is typed as a string throughout, so clients have to `JSON.parse(bucket.key)` to get the components back. Sub-aggregations nest under `sub_aggregations`.

## Reranking

Cross-encoder reranking over the top-N results:

```json
{
  "reranker": {
    "provider": "antfly",
    "model": "mixedbread-ai/mxbai-rerank-base-v1",
    "field": "content"
  }
}
```

Providers: only `antfly` (local ONNX inference) executes. `ollama`, `cohere`, and `vertex` are accepted by the schema and pass config validation, but the runtime dispatch has no branch for them — the query runs retrieval and then fails with **HTTP 400** (`invalid query request`). `field` selects the document text to score; `template` renders it instead if you need more than one field.

Reranking runs after retrieval and merge. Best practice: retrieve 50–100 candidates, then rerank down to the final size.

## Pagination

- `limit` — max results (semantic search treats this as topk; default varies by query type, typically 10)
- `offset` — skip N results. Supported for text-backed, `match_all`, and filter-only queries. With `semantic_search` the request is rejected with **HTTP 422** (`unsupported query request`)
- `search_after` / `search_before` — cursor pagination. Pass the previous page's boundary hit `_sort` tuple **exactly**, including the appended `_id` tie-breaker, preserving JSON types. Mutually exclusive with `offset`, and likewise unsupported for `semantic_search` and count-only queries

```json
{ "order_by": [{"field": "created_at", "desc": true}], "search_after": ["2026-05-01T00:00:00Z", "doc-417"] }
```

With no `order_by`, the effective order is `_id` ascending and the cursor tuple is a single `_id` string.

## Sorting

`order_by` — array of `{field, desc}`:
```json
{ "order_by": [ { "field": "created_at", "desc": true } ] }
```

- The field must be declared sortable — either `x-antfly-field` with `sortable: true`, or a matching `dynamic_templates[].mapping` with `sortable: true`. `_id` is always sortable. Anything else returns **HTTP 422** rather than silently falling back
- Antfly appends `_id` ascending as a stable tie-breaker when you omit it
- Semantic queries are always ranked by similarity — supplying `order_by` (including on `_score`) is rejected
- Not supported together with `count: true`

## Field Projection

`fields` — array of fields to include in hits:
```json
{ "fields": ["title", "price", "category"] }
```

Supports nested paths. **Required** whenever `hierarchy.group_by` or `hierarchy.children` is present — use `[]` for identity-only groups.

## Hierarchy

`hierarchy` reshapes results around extracted document structure. Levels are `source` and `unit`.

- `hierarchy.group_by: {"level": "source" | "unit", "matches": {...}}` — group index matches at a level; nested `matches` default to three hits per group while `limit` controls the number of groups. Unit groups are relevance-ranked and reject `order_by`/`search_after`/`search_before`
- `hierarchy.ancestors: {"source": {...}, "unit": {...}}` — project ancestor context onto each hit without changing cardinality
- `hierarchy.children: {"parent": {"level": "source", "id": "..."}, "level": "unit"}` — sequential browse of every unit in a source revision, including empty ones. Requires `order_by: [{"field": "_hierarchy.position"}]` ascending, pages of 1–100, and cursor pagination via the two-string `_sort` tuple. A cursor whose source revision changed returns 409

An empty `hierarchy: {}` returns direct index matches. `group_by` and `children` are mutually exclusive.

## Graph Searches

`graph_searches` — a map of name → graph query, executed after the full-text/vector phase. Types: `traverse`, `neighbors`, `shortest_path`, `k_shortest_paths`, `pattern`. Start/target nodes come from explicit `keys` or a `result_ref` selector, optionally narrowed by `node_filter`. The recognized selectors are an exact named result-set name, the bare `"$full_text_results"` / `"$fused_results"` / `"$embeddings_results"`, and the suffixed `"$full_text_results.<n>"`, `"$aknn_results.<n>"`, `"$graph_results.<n>"`. To pick a single vector index, use the bare index name or `"$aknn_results.<index>"` — `"$embeddings_results.<index>"` has no resolution branch and fails with `GraphResultRefNotImplemented`. Results land in `graph_results`; `expand_strategy` (`union` or `intersection`) controls how they merge with search hits.

## Joins

`join` — cross-table join. `join_type` is `inner`, `left`, or `right`; `on` names `left_field`/`right_field`; `right_filters` narrows the joined side; `nested_join` chains further tables. Strategies (`broadcast`, `index_lookup`, `shuffle`) are auto-selected by table size and can be forced.

Projection is two-sided. Top-level `fields` projects the **left** table only — `"fields": ["customers.name"]` is silently ineffective, not an error. Select right-side columns with `join.right_fields`, listing them **unprefixed** (`"right_fields": ["name"]`). The `<right_table>.<field>` dotting only appears on the way out, as the merged key in each hit's `_source`.

## Foreign Sources

`foreign_sources` — map of table name → external source config (e.g. Postgres). When a table named here appears as the query table or a join's `right_table`, the query is routed to the external database instead of Antfly shards.

Foreign tables support `filter_query`, field selection, `limit`/`offset`, and aggregations (executed against the external source). Full-text search, semantic search, exclusion queries, graph searches, rerankers, analyses, and cursor pagination (`search_after`/`search_before`) are rejected on them.

## Multi-Query

`POST /db/v1/query` with `Content-Type: application/x-ndjson`, one JSON object per line, each line newline-terminated. Results come back in `responses`, in request order.

## Sharp Edges

1. **`semantic_search` with no `indexes` entry at all is rejected with HTTP 422** (`unsupported query request`) — not an empty result set. A *typo'd* index name is a different failure: `indexes` naming an index that does not exist raises `EmbeddingIndexNotFound`, which is not in the query error switch, so it falls through to a **500** (`query failed`). Check the index name first when a semantic query 500s.
2. **Inside `full_text_search`, ranges are flat and geo takes `location: [lon, lat]`** — the `lat`/`lon` keys are not the request contract, and the wrapped `numeric_range`/`term_range`/`date_range`/`range`/`geo_bbox`/`geo_distance`/`geo_shape`/`ip_range`/`bool_field`/`doc_id`/`exists`/`terms`/`ref` forms belong to structured `filter_query`/`exclusion_query`.
3. **`distance_over` excludes the most similar hits** — it is a minimum distance. `distance_under` is the one that filters weak matches.
4. **`filter_query` is applied before scoring**, so it changes which documents compete, not just which survive.
5. **Facets are mapping-independent** — terms aggregations read stored JSON, so `keyword` is not required for faceting.
6. **`offset` is text-only** — with `semantic_search` the request is rejected with HTTP 422 (`unsupported query request`). Use `search_after`/`search_before` for deep pages of exact queries.
7. **`order_by` needs a `sortable: true` mapping** — from `x-antfly-field` or a dynamic template; `_id` is always sortable, anything else is a 422. Semantic queries reject `order_by` entirely.
8. **The query-string grammar is Antfly's own Lucene-style subset**, not Bleve or Elasticsearch parity. `zig/QUERY_STRING.md` is the contract.
9. **Multi-query uses NDJSON**, not a JSON array, and always answers with `{"responses": [...]}`.
10. **`fields` is required** when `hierarchy.group_by` or `hierarchy.children` is present.
