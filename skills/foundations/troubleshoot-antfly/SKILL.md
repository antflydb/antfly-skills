---
name: troubleshoot-antfly
description: Diagnose Antfly Cloud, local runtime, MCP, ingestion, indexing, query, inference, timeout, and retrieval-agent failures. Use when Antfly returns authentication errors, empty or poor results, incomplete indexes, invalid requests, connection closures, slow retrieval, missing images, or agent grounding failures.
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

- `401/403`: credential, header, scope, or RBAC.
- Empty semantic hits with lexical hits: index name/readiness/model/template.
- Empty evidence with document metadata: hierarchy or stored-content selection.
- `524` or non-JSON proxy body: upstream timeout; parse by content type before JSON.
- MCP schema rejection: use the live describe tools; do not invent fields.
- Missing image previews: private object access is separate from image embedding/search.

Do not implement a destructive repair unless the user explicitly asks for it.
