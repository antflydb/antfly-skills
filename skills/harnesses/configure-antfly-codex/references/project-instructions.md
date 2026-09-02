# Project instruction fragment

- Use Antfly MCP as the evidence source for questions covered by the configured knowledge table.
- Use only `query` and `get_document` during normal support retrieval.
- Use discovery tools only for explicit setup or diagnosis.
- Never mutate Antfly data, tables, indexes, backups, or permissions from a retrieval task.
- Keep `tableName` outside raw `queryRequest`; specify the embeddings index for semantic search.
- Build factual answers from returned explanatory content and cite public sources.
- Stop on authentication, authorization, invalid-request, or tool-level errors.
