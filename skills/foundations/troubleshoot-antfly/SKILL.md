---
name: troubleshoot-antfly
description: Diagnose Antfly Cloud, local runtime, MCP, ingestion, indexing, query, inference, timeout, and retrieval-agent failures. Use when Antfly returns authentication errors, refuses to start, empty or poor results, incomplete indexes, invalid requests, stale cursors, oversized MCP results, connection closures, slow retrieval, missing images, uncertain write outcomes, or agent grounding failures.
---

# Troubleshoot Antfly

Isolate the failing layer before changing configuration.

## Diagnostic order

1. Capture the exact status, error body, request ID, endpoint class, and operation without secrets.
2. Check authentication and authorization. Stop on 401 or 403.
3. Check instance health and MCP initialization.
4. Verify the table, sample data, expected fields, and source ingestion status.
5. Verify index existence, model availability, enrichment progress, and readiness.
6. Validate the query against `describe_query_request` and test the simplest lexical query.
7. Add semantic search, fusion, hierarchy, reranking, or generation one layer at a time.
8. Separate retrieval latency from model generation latency.
9. Retest with a known fixture and document the actual root cause.

## Common classifications

- `401/403`: credential, header, scope, or RBAC. On Antfly Cloud MCP, 403 also means the key
  belongs to a different instance than the URL, or the request carried an `Origin` header
  (hosted MCP is for backends, not browser code).
- Auth-enabled server refuses to start: set `ANTFLY_BOOTSTRAP_ADMIN_PASSWORD` (12–72 bytes)
  on first start; legacy `admin:admin` instances refuse to start until it is supplied.
- Public `/ai/v1` inference returns 403: it is disabled by default; enable it with
  `{"public_inference": {"enabled": true}}`. Indexing and query-time model calls are unaffected.
- MCP `400` with no session ID: send the `Mcp-Session-Id` from `initialize`. `404` unknown
  session: run `initialize` again.
- MCP tool error about result size: results over `mcp.max_tool_result_bytes` (96 KiB default)
  are replaced with an error, never truncated. Reduce `limit` or project focused `fields`;
  never request `_chunks.*`.
- Empty semantic hits with lexical hits: index name/readiness/model/template.
- Whole source documents instead of chunks, or empty evidence with document metadata: add
  `"hierarchy": {}` (omitting it returns the v0.2-compatible source-grouped shape), then check
  stored-content selection and `fields`.
- `409` `hierarchy_cursor_stale`: the source revision changed during `children` traversal.
  Restart without `search_after`; retrying the same cursor cannot succeed.
- `524` or non-JSON proxy body: upstream timeout; parse by content type before JSON.
- Retrieval agent returns SSE when JSON was expected: `stream` defaults to true; send
  `"stream": false` for one JSON body.
- MCP schema rejection: use the live describe tools; do not invent fields.
- Missing image previews: private object access is separate from image embedding/search.

## Write retries

A missing response does not prove a write failed. Check document or write status before
retrying, and make retried writes idempotent (stable keys). SDK mutation results distinguish
committed, pending, and repair-required outcomes.

Do not implement a destructive repair unless the user explicitly asks for it.
