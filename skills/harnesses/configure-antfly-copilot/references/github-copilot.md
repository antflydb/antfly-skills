# VS Code MCP configuration

```json
{
  "servers": {
    "antfly": {
      "type": "http",
      "url": "https://platform.antfly.io/cloud/v1/<instance_id>/mcp/v1",
      "headers": {
        "Authorization": "Bearer antflydb_<key>"
      }
    }
  }
}
```

Keep placeholders in shared files. A read-only key should expose discovery and
query tools, and must hide `batch`, create/drop, backup, and restore tools.

Smoke test:

> List the Antfly MCP tools you can use, then list the available Antfly tables.
