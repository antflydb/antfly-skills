---
name: connect-antfly-mcp
description: Configure and verify a local, self-hosted, or Antfly Cloud MCP connection for an agent harness. Use when connecting an agent to Antfly, creating a scoped API key, setting an MCP URL or API key, applying a read-only tool policy, checking authentication, or smoke-testing MCP capabilities.
---

# Connect Antfly MCP

Connect an agent to Antfly without exposing broader permissions than its task requires.

## Workflow

1. Determine whether the target is Antfly Cloud or a self-hosted/local Antfly server. Both are
   first-class MCP targets.
2. Obtain the exact MCP endpoint. Self-hosted: `<server>/mcp/v1` on the API port (no extra
   process or flag). Cloud: `https://platform.antfly.io/cloud/v1/<instance_id>/mcp/v1`. Do not
   infer a Cloud path from a generic base URL. Use HTTPS except on loopback.
3. Use a dedicated key scoped to the task. For support and retrieval agents, require read-only
   access. Cloud: an instance key of type read only. Self-hosted: see "Self-hosted keys".
4. Keep the key in the harness secret store or environment. Never write its plaintext value into a repository.
5. Configure Streamable HTTP MCP using the harness-specific skill when one exists.
6. Initialize the connection and call `describe_mcp_capabilities`.
7. Call `list_tables`, then make one known read-only `query` against the intended table.
   Self-hosted, `list_tables` needs read on at least one table and returns only readable
   tables, so table-scoped keys work. Antfly Cloud documents that `list_tables` succeeds only
   for a key that can read every table; with a table-scoped Cloud key, skip it and query the
   known table directly.
8. Record the endpoint class, permitted tools, table, index, and successful smoke-test date without recording the key.

## Self-hosted keys

An auth-enabled server's first start requires `ANTFLY_BOOTSTRAP_ADMIN_PASSWORD` (12–72 bytes),
which becomes the `admin` password; an instance still on legacy `admin:admin` refuses to start.
With auth off, MCP is unauthenticated and offers every tool — do not share it with an agent.

Create a narrowed key for an existing user (`expires_in` is optional):

```bash
curl -s -u "admin:$ANTFLY_ADMIN_PASSWORD" -X POST "$ANTFLY_URL/auth/v1/users/{user}/api-keys" \
  -H "Content-Type: application/json" \
  -d '{"name": "agent", "expires_in": "720h",
       "permissions": [{"resource": "docs", "resource_type": "table", "type": "read"}]}' \
  | jq -r .encoded
```

Use the `encoded` value as `Authorization: Bearer <encoded>`; it is shown once. The key acts
as its owner narrowed by its permissions, and inherits the owner's row filters. For per-caller
scope behind a gateway, see `references/backend/auth.md` (trusted-principal tokens).

## Tool boundary

For retrieval-only agents, allow `query` and `get_document` during normal use.
Enable `list_tables`, `describe_table`, `list_indexes`, `describe_indexes`,
`sample_documents`, `describe_query_request`, and `describe_mcp_capabilities`
only for setup or diagnosis. Enforce this as an allowlist: deny every other tool,
including mutation, backup, restore, and any tools installed extensions add.

## Failure behavior

- Stop on 401 or 403; do not try another credential automatically. On Cloud, 403 also means
  the key belongs to another instance or the request carried an `Origin` header.
- A missing `Mcp-Session-Id` returns 400; an unknown session returns 404 — re-initialize.
- Treat an MCP response with `isError: true` as a failure.
- On a transient connection failure, reconnect once outside the model tool loop.
- Do not change tables, indexes, or permissions merely to make a smoke test pass.

Run `scripts/check-env.sh` to validate the required local environment without
printing the credential. See `references/verification.md` for the acceptance checklist.
