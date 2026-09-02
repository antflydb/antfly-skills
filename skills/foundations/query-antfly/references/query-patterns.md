# Query patterns

## Semantic

```json
{
  "semantic_search": "expanded conceptual intent",
  "indexes": ["{{VECTOR_INDEX}}"],
  "hierarchy": {"return_level": "chunk"},
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
  "hierarchy": {"return_level": "chunk"},
  "limit": 6
}
```

These are patterns, not a frozen API schema. Keep the direct-chunk hierarchy
setting for grounded retrieval. Do not add `fields`, hierarchy `include`, source
rollup, or `max_children_per_parent` unless a live regression test proves that
the returned explanatory chunk text is preserved. Use `describe_query_request`
to confirm other graph, rendering, filtering, and analysis fields against the
connected server.
