---
name: query-antfly
description: Design, execute, and evaluate Antfly full-text, semantic, hybrid, filtered, or graph retrieval queries. Use when choosing retrieval strategy, constructing QueryRequest bodies, improving relevance or latency, diagnosing empty results, or retrieving grounded evidence from an Antfly table.
---

# Query Antfly

Build the smallest valid query that answers the retrieval need.

## Workflow

1. Identify the table, searchable text field, and embeddings index.
2. Classify intent:
   - exact identifiers, commands, errors, or field names: full text or hybrid;
   - concepts and paraphrases: semantic;
   - mixed intent: hybrid with RRF;
   - relationships: `graph_queries` on a graph index (`graph_searches` is deprecated), or Cypher at `/db/v1/graphs/{graph}/query`;
   - strict scope: add filters, never encode authorization only in prompt text.
3. Call `describe_query_request` when the live request shape is uncertain.
4. Keep `tableName` outside raw `queryRequest` in MCP calls.
5. Specify `indexes` for semantic retrieval.
6. Send `"hierarchy": {}` for direct chunk/index matches. Omitting `hierarchy` returns the v0.2-compatible source-grouped shape. Add `group_by` (`source` or `unit`), `ancestors`, or `children` only when needed (see `references/query-patterns.md`).
7. Project focused `fields` (for example the text field you cite) and never `_chunks.*`, which expands the whole stored chunk array. MCP tool results are capped (96 KiB by default, `mcp.max_tool_result_bytes`); an oversized result is an error, not a truncation. `fields` is required with source `group_by` and with `children`.
8. Evaluate explanatory content, ranking, latency, and source coverage—not just hit count.
9. Change one query variable at a time and preserve a repeatable evaluation case.

## Safe defaults

- Start with five or six results.
- Use RRF for keyword-plus-vector fusion.
- Prefer direct chunk-level explanatory evidence for RAG.
- Do not fan out concurrent queries by default.
- Treat empty results as a retrieval diagnostic, not proof that information is absent.

See `references/query-patterns.md` for canonical raw requests.
