# Support retrieval contract

## Intent routing

- Definitions, overviews, architecture, use cases, and paraphrases: one expanded semantic query.
- APIs, commands, errors, configuration fields, and procedures: one full-text plus semantic query fused with RRF.
- Include only the configured embeddings index and default to six results.
- Keep `tableName` outside raw `queryRequest`.

## Call budget

Make one initial query. Make at most one sequential focused fallback only when
the first result has no usable evidence or lacks required coverage. Never run
parallel Antfly retrieval calls by default.

## Evidence

Evidence must include explanatory stored or extracted content. Preserve useful
chunks even when they share one source. Remove embeddings, provenance noise,
internal IDs, and transport metadata before generation. Deduplicate displayed
citations independently from evidence selection.

Return only sources cited in the answer. Convert private source paths to public
documentation URLs and never expose an S3/R2 path in a public response.

## Failures

- Authentication/authorization: stop and report configuration failure.
- Invalid request: validate against `describe_query_request`; do not let the model invent a new schema.
- Empty results: permit one focused fallback.
- Timeout/connection/transient 5xx: one transport reconnect outside the agent loop, then fail safely.
- MCP `isError: true`: classify as failure even if HTTP succeeded.
- Insufficient evidence: answer only confirmed facts and use configured escalation.

## Observability

Record request ID, table, strategy, tool calls, fallback use, connection/query/
generation/total latency, hit/source counts, decoded bytes, reconnects, and
failure class. Never log credentials or authorization headers.
