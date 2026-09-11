# Query patterns

## Semantic

```json
{
  "semantic_search": "expanded conceptual intent",
  "indexes": ["{{VECTOR_INDEX}}"],
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
  "limit": 6
}
```

These are patterns, not a frozen API schema. Chunk-level hits come back
directly; use `hierarchy` only to group results or fetch ancestors/children —
grouping levels are `source` and `unit`, and a `return_level` field does not exist — per
`references/backend/search.md`. Do not add `fields` projection or source
rollup unless a live regression test proves the returned explanatory chunk
text is preserved. Use `describe_query_request`
to confirm other graph, rendering, filtering, and analysis fields against the
connected server.
