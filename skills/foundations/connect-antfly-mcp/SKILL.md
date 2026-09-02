---
name: connect-antfly-mcp
description: Configure and verify a local or hosted Antfly MCP connection for an agent harness. Use when connecting an agent to Antfly, setting an MCP URL or API key, applying a read-only tool policy, checking authentication, or smoke-testing MCP capabilities.
---

# Connect Antfly MCP

Connect an agent to Antfly without exposing broader permissions than its task requires.

## Workflow

1. Determine whether the target is Antfly Cloud or a local Antfly instance.
2. Obtain the exact MCP endpoint from the instance. Do not infer a Cloud path from a generic base URL.
3. Use a dedicated, instance-scoped API key. For support and retrieval agents, require read-only access.
4. Keep the key in the harness secret store or environment. Never write its plaintext value into a repository.
5. Configure Streamable HTTP MCP using the harness-specific skill when one exists.
6. Initialize the connection and call `describe_mcp_capabilities` when available.
7. Call `list_tables`, then make one known read-only `query` against the intended table.
8. Record the endpoint class, permitted tools, table, index, and successful smoke-test date without recording the key.

## Tool boundary

For retrieval-only agents, allow `query` and `get_document` during normal use.
Enable `list_tables`, `describe_table`, `list_indexes`, `describe_indexes`,
`sample_documents`, `describe_query_request`, and `describe_mcp_capabilities`
only for setup or diagnosis. Deny mutation, backup, and restore tools.

## Failure behavior

- Stop on 401 or 403; do not try another credential automatically.
- Treat an MCP response with `isError: true` as a failure.
- On a transient connection failure, reconnect once outside the model tool loop.
- Do not change tables, indexes, or permissions merely to make a smoke test pass.

Run `scripts/check-env.sh` to validate the required local environment without
printing the credential. See `references/verification.md` for the acceptance checklist.
