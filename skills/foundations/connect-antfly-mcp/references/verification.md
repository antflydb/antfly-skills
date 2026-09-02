# Connection verification

## Inputs

- `ANTFLY_MCP_URL`: exact instance MCP endpoint.
- `ANTFLY_API_KEY`: dedicated key in a secret store or environment.
- Expected table and embeddings index.

## Acceptance

1. MCP initialization succeeds.
2. Capability discovery returns the current server tool list.
3. The expected table and index are visible.
4. A known query returns explanatory content.
5. Mutation tools are absent or rejected for the retrieval credential.
6. Logs contain no authorization header or key.

Do not hard-code a fixed tool count. Antfly MCP evolves; discover the current
surface through the server and test the required/denied capabilities by name.
