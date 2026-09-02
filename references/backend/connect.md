# Connect — Auth, Client Setup, SDKs

## API Base URLs

There is no `/api/v1`. The public surface is split across five bases:

| Base | Covers |
|------|--------|
| `{{ANTFLY_API_URL}}/db/v1` | tables, indexes, documents, batch, merge, query, agents, transactions |
| `{{ANTFLY_API_URL}}/auth/v1` | users, API keys, permissions, row filters |
| `{{ANTFLY_API_URL}}/ai/v1` | inference: embed, chunk, rerank, generate, extract, models |
| `{{ANTFLY_API_URL}}/ml/v1` | traditional ML predictors: `models` catalog, `predict` on feature vectors |
| `{{ANTFLY_API_URL}}/extensions/v1` | extension lifecycle: packages, install, update, enable/disable, drop, config |

The same listener also serves the agent-protocol surfaces `{{ANTFLY_API_URL}}/mcp/v1` (MCP) and `{{ANTFLY_API_URL}}/a2a` (A2A), which sit outside the versioned bases.

Health and readiness: `GET /healthz` and `GET /readyz` — served at the root of the main public API listener (8080), not under a versioned base. The dedicated health port serves the same two probes plus `GET /metrics`.

## Authentication Methods

Three schemes, all on the `Authorization` header. There is no OAuth scheme.

**API Key** (most common):
```
Authorization: ApiKey base64(key_id:key_secret)
```
The value is `ApiKey ` followed by base64 of `key_id:key_secret` (colon-joined). Not just the secret. Key creation returns a ready-made `encoded` field with exactly this base64 value.

**Bearer** — the same credential, different prefix. Not an OAuth token:
```
Authorization: Bearer base64(key_id:key_secret)
```

**Basic Auth**:
```
Authorization: Basic base64(username:password)
```

## SDKs

**TypeScript** (`@antfly/sdk` on npm):
- `new AntflyClient({ baseUrl, auth })` — auth accepts `{ username, password }`, `{ type: "basic", username, password }`, `{ type: "apiKey", keyId, keySecret }`, or `{ type: "token", token }`
- Namespaces: `client.tables.*`, `client.indexes.*`, `client.users.*`; plus `client.query()`, `client.multiquery()`, `client.linearMerge()`, `client.multiBatch()`, `client.retrievalAgent()`, `client.queryBuilderAgent()`
- Streaming support for the retrieval agent via callbacks (`onHit`, `onGeneration`, `onReasoning`, `onFollowup`, `onConfidence`, etc.)

**Go** (`github.com/antflydb/antfly/go/pkg/sdk`, package `sdk`):
- `sdk.NewAntflyClientWithOptions(url, oapi.WithRequestEditorFn(sdk.WithApiKey(keyID, keySecret)))` — `WithApiKey`, `WithToken`, and `WithBasicAuth` return `oapi.RequestEditorFn`, while the constructor takes `oapi.ClientOption`, so they must be wrapped. `oapi` is `github.com/antflydb/antfly/go/pkg/sdk/oapi`
- `sdk.NewAntflyClientWithToken(baseURL, httpClient, token)` wraps that for bearer tokens
- `sdk.NewAntflyClient(baseURL, httpClient)` is the unauthenticated constructor
- Methods mirror the REST API: `CreateTable`, `Batch`, `LinearMerge`, `Query`, `LookupKey`, etc.

**Python** (`antfly-sdk` on PyPI, imported as `antfly`):
- Full client matching the REST API

**Rust**:
- `rs/crates/sdk` — `antfly-sdk`, an async client generated from the OpenAPI spec
- `rs/crates/pgaf` — `pgaf`, a PostgreSQL extension (pgrx) for querying Antfly from SQL

## Sharp Edges

- API key format: `base64(key_id:key_secret)` — forgetting the key ID is a common mistake. Use the `encoded` value returned at creation.
- `Bearer` carries the same base64 credential as `ApiKey`; it is not an OAuth access token.
- Base path depends on the resource: database calls are `/db/v1`, user and key calls are `/auth/v1`, inference calls are `/ai/v1`, tabular predictors are `/ml/v1`, extension lifecycle is `/extensions/v1`.
- Health endpoints are at the root (`/healthz`, `/readyz`) on the main API listener, not under a versioned base; `/metrics` is only on the health port.
- Go auth helpers are request editors, not client options — `oapi.WithRequestEditorFn(...)` is required or the code will not compile.
- SDK auth config differs per language — check the SDK for exact constructor args.
