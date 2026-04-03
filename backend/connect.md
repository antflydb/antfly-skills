# Connect — Auth, Client Setup, SDKs

## API Base URL

All API requests go to `{{ANTFLY_API_URL}}/api/v1`.

Health check: `GET {{ANTFLY_API_URL}}/healthz`

## Authentication Methods

**API Key** (most common for Cloud):
```
Authorization: ApiKey base64(keyID:keySecret)
```
The header value is the string "ApiKey " followed by base64 encoding of `keyID:keySecret` (colon-separated). Not just the secret.

**Bearer Token**:
```
Authorization: Bearer <token>
```

**Basic Auth**:
```
Authorization: Basic base64(username:password)
```

**OAuth**: Cloud supports OAuth 2.0. Authorization and token endpoints are Cloud-specific.

## SDKs

**TypeScript** (`@antfly/sdk` on npm):
- `new AntflyClient({ baseUrl, auth })` — auth accepts `{ username, password }`, `{ type: "apiKey", keyId, keySecret }`, or `{ type: "bearer", token }`
- Methods: `client.tables.*`, `client.indexes.*`, `client.users.*`, `client.query()`, `client.agents.retrieval()`
- Streaming support for RAG via callbacks (`onHit`, `onGeneration`, `onReasoning`, etc.)
- Multi-query via `client.multiquery()`

**Go** (`github.com/antflydb/antfly/pkg/client`):
- `client.NewAntflyClientWithOptions(url, WithApiKey(id, secret))` or `WithBearerToken(token)` or `WithBasicAuth(user, pass)`
- Methods mirror the REST API: `CreateTable`, `Batch`, `LinearMerge`, `Query`, `LookupKey`, etc.

**Python** (`antfly` on PyPI):
- Full client matching the REST API

**Rust** (`pgaf`):
- PostgreSQL extension — query Antfly tables from Postgres via SQL

## Sharp Edges

- API key format: `base64(keyID:keySecret)` — forgetting to include the keyID is a common mistake
- SDK auth config differs per language — check the SDK docs for exact constructor args
- Health endpoint is at the root (`/healthz`), not under `/api/v1/`
