# Search — Full-Text, Vector, Hybrid Queries

## Query Endpoint

`POST /api/v1/query`

A single query request can combine multiple search strategies. The response includes `hits`, optional `aggregations`, optional `graph_results`, and optional `join_result`.

## Full-Text Search (BM25)

`full_text_search` — uses Bleve query DSL.

### Query Types

| Query | Syntax | Example |
|-------|--------|---------|
| Match | `{ "match": "laptop", "field": "title" }` | Tokenized search |
| Term | `{ "term": "electronics", "field": "category" }` | Exact match |
| Match Phrase | `{ "match_phrase": "high performance", "field": "desc" }` | Exact phrase |
| Fuzzy | `{ "fuzzy": "latop", "field": "title" }` | Typo-tolerant |
| Prefix | `{ "prefix": "electr", "field": "category" }` | Prefix match |
| Wildcard | `{ "wildcard": "lap*", "field": "title" }` | Glob pattern |
| Numeric Range | `{ "numeric_range": { "field": "price", "min": 100, "max": 500 } }` | Number range |
| Date Range | `{ "date_range": { "field": "created", "start": "2026-01-01" } }` | Date range |
| Geo Distance | `{ "geo_distance": { "field": "location", "lat": 37.7, "lon": -122.4, "distance": "5km" } }` | Radius search |
| Match All | `{ "match_all": {} }` | Everything |

### Boolean Combinations

- **AND**: `{ "conjuncts": [ query1, query2 ] }`
- **OR**: `{ "disjuncts": [ query1, query2 ] }`

### String Query Shorthand

`{ "query": "title:laptop AND price:<2000" }` — Bleve query string syntax. Supports field-scoped terms, boolean operators, ranges.

## Semantic Search (Vector)

`semantic_search` — pass a text string, Antfly embeds it and finds similar documents.

**Required**: `indexes` array specifying which embeddings index(es) to search.

```json
{
  "table": "products",
  "semantic_search": "comfortable office chair for long hours",
  "indexes": ["product_embeddings"],
  "limit": 20
}
```

Optional distance filters:
- `distance_over` — minimum similarity (exclude low-relevance results)
- `distance_under` — maximum distance

## Hybrid Search

Combine `full_text_search` + `semantic_search` in one query. Results are merged using Reciprocal Rank Fusion (RRF).

```json
{
  "table": "products",
  "full_text_search": { "query": "ergonomic chair" },
  "semantic_search": "comfortable seating for office work",
  "indexes": ["product_embeddings"],
  "limit": 15
}
```

RRF combines rankings from both result sets. Documents appearing in both get a boost.

## Filters

**filter_query** — must match, but doesn't affect relevance scoring:
```json
{
  "filter_query": { "term": "electronics", "field": "category" }
}
```

**exclusion_query** — must NOT match:
```json
{
  "exclusion_query": { "term": "discontinued", "field": "status" }
}
```

**filter_prefix** — filter by key prefix (for multi-tenant or hierarchical data):
```json
{
  "filter_prefix": "tenant:acme:"
}
```

Filters use the same Bleve query syntax as `full_text_search`.

## Aggregations / Facets

Facet-style counts are implemented through `aggregations`.

Example:
```json
{
  "aggregations": {
    "categories": {
      "type": "terms",
      "field": "category"
    }
  }
}
```

Results come back under `aggregations.<name>.buckets` with `key` and `doc_count`.

Facets require `keyword` typed fields — `text` fields are tokenized and won't produce meaningful facet values.

## Reranking

Cross-encoder reranking for improved relevance on the top-N results:

```json
{
  "reranker": {
    "provider": "termite",
    "model": "mxbai-rerank-base-v1"
  }
}
```

Providers: `termite` (local ONNX), `ollama`, `openai`.

Reranking is applied after initial retrieval and RRF merge.

## Pagination

Current query pagination is offset-based for full-text queries:

- `offset` — number of results to skip
- `limit` — max results to return

`offset` is not supported for `semantic_search`.

## Sorting

`order_by` — array of sort fields with direction:
```json
{
  "order_by": [
    { "field": "created_at", "desc": true },
    { "field": "_score", "desc": true }
  ]
}
```

## Field Projection

`fields` — array of fields to include in results:
```json
{
  "fields": ["title", "price", "category"]
}
```

Reduces response size. Supports nested paths.

## Multi-Query

`POST /api/v1/query` with `Content-Type: application/x-ndjson`

Multiple queries in a single request, one JSON object per line. Results returned as array.

## Additional Query Features

- `aggregations` — metrics and bucketing aggregations
- `tree_search` — hierarchical / tree traversal search
- `graph_searches` — declarative graph traversals
- `join` — join query results with another table
- `foreign_sources` — federated query-time access to external sources used with joins

## Sharp Edges

1. **`semantic_search` without `indexes` returns nothing** — no error, just zero results. Always specify the index name.
2. **Facets require `keyword` fields** — `text` fields are tokenized and produce meaningless facet values.
3. **`filter_query` doesn't affect scoring** — it's a post-filter. Use `full_text_search` if relevance should be affected.
4. **`offset` is only for full-text queries** — semantic search does not support offset pagination.
5. **Bleve query string syntax** differs from Elasticsearch — use Bleve docs as reference, not ES.
6. **Multi-query uses NDJSON** (newline-delimited JSON), not a JSON array.
7. **`order_by` is an array** of `{ field, desc }` objects, not a map.
8. **`limit`** defaults vary — always specify explicitly for predictable results.
