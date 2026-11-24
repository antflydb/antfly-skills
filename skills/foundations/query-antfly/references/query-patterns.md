# Query patterns

## Semantic

```json
{
  "semantic_search": "expanded conceptual intent",
  "indexes": ["{{VECTOR_INDEX}}"],
  "fields": ["text"],
  "hierarchy": {},
  "limit": 6
}
```

## Hybrid

```json
{
  "full_text_search": {"match": "exact terms", "field": "text"},
  "semantic_search": "expanded question intent",
  "indexes": ["{{VECTOR_INDEX}}"],
  "merge_config": {"strategy": "rrf"},
  "fields": ["text"],
  "hierarchy": {},
  "limit": 6
}
```

These are patterns, not a frozen API schema; replace `text` with the stored
field you cite.

- `"hierarchy": {}` returns direct chunk/index matches. Omitting `hierarchy`
  keeps the v0.2-compatible source-grouped shape.
- Inside `hierarchy`, `group_by.level` is `source` or `unit`; `ancestors` adds
  projected context without changing cardinality; `children` is a separate
  sequential traversal paginated with `_sort`/`search_after`. A `409`
  `hierarchy_cursor_stale` means the source revision changed: restart the
  traversal without `search_after`.
- Project focused `fields`; never request `_chunks.*`. Source `group_by` and
  `children` require explicit `fields` (`[]` for identity only). Over MCP, an
  oversized result (96 KiB default) returns an error asking for a smaller
  `limit` or `fields`.
- Fusion strategies are `rrf` (default) and `rsf`.
- Graph: use `graph_queries` (`graph_searches` is a deprecated alias), or Cypher
  at `/db/v1/graphs/{graph}/query` for named graphs.

See `references/backend/search.md`, and use `describe_query_request` to confirm
graph, rendering, filtering, and analysis fields against the connected server.
