# TypeScript SDK — `@antfly/sdk`

## Installation

```
npm install @antfly/sdk
```

ES module + CommonJS. Full TypeScript types included. Only runtime dependency: `openapi-fetch`.

## Client Initialization

```typescript
import { AntflyClient } from '@antfly/sdk'

const client = new AntflyClient({
  baseUrl: '{{ANTFLY_API_URL}}',
  auth: { type: 'apiKey', keyId: '...', keySecret: '...' },
  headers: { 'X-Trace': 'demo' }   // optional
})
```

`baseUrl` is the server root. It is trimmed, then exactly **one** trailing slash is stripped, then a trailing `/db/v1`, `/auth/v1`, or `/ai/v1` — in that order. So `https://host`, `https://host/`, and `https://host/db/v1/` all normalise to `https://host`, but a doubled trailing slash leaves one behind.

`Client` (also the default export) bundles the database client and the inference client:

```typescript
import { Client } from '@antfly/sdk'

const sdk = new Client({ baseUrl: '...', inferenceBaseUrl: '...', auth: { ... } })
sdk.antfly.tables.list()      // AntflyClient
sdk.inference.embed('bge-small-en-v1.5', 'text')  // InferenceClient
```

### Auth Options

| Type | Config | Header sent |
|------|--------|-------------|
| API Key | `{ type: 'apiKey', keyId, keySecret }` | `ApiKey base64(keyId:keySecret)` |
| Token | `{ type: 'token', token }` | `Bearer <token>` |
| Basic | `{ type: 'basic', username, password }` | `Basic base64(user:pass)` |
| Basic (legacy) | `{ username, password }` — no `type` | `Basic base64(user:pass)` |

`client.setAuth(auth)` or `client.setAuth(username, password)` swaps credentials and rebuilds the internal client.

## Methods

### Cluster
- `client.getStatus()` — cluster status
- `client.getClusterStatus()` — topology and data placement
- `client.connections.list({ types?, include?, refresh?, signal? })` — configured inference/web-search/IO/CDC connections

### Tables
- `client.tables.list({ prefix?, pattern? })`
- `client.tables.get(tableName)` — schema, indexes, shards
- `client.tables.create(tableName, config?)` — `config` is a `CreateTableRequest` (`num_shards`, `schema`, indexes …)
- `client.tables.drop(tableName)`
- `client.tables.updateSchema(tableName, schema)`
- `client.tables.batch(tableName, { inserts?, deletes?, transforms?, sync_level? })`
- `client.tables.batchWithOptions(tableName, request, { maxRequestBytes?, maxResponseBytes?, signal? })`
- `client.tables.lookup(tableName, key, { fields? })` — `fields` here is a comma-separated **string** (`"title,author,metadata.tags"`), not an array like everywhere else
- `client.tables.scan(tableName, request?)` — async generator over NDJSON documents
- `client.tables.scanAll(tableName, request?)` — same, collected into an array
- `client.tables.backup(tableName, request)` / `client.tables.restore(tableName, request, { idempotencyKey? })`
- `client.tables.artifacts.*` — generated-artifact enrichments and reprocess jobs
- `client.multiBatch({ tables, sync_level? })` — atomic cross-table batch
- `client.linearMerge(tableName, request)`
- `client.restoreJobs.startCluster/get/list/listAll/cancel`

### Queries
- `client.query(request, { signal? })` — returns the **first** `QueryResult`
- `client.multiquery(requests)` — returns `QueryResponses` (NDJSON internally)
- `client.tables.query(tableName, request, { signal? })` — table-scoped, returns `QueryResponses`
- `client.tables.multiquery(tableName, requests)`

### Indexes
- `client.indexes.list(tableName)` / `client.indexes.get(tableName, indexName)`
- `client.indexes.create(tableName, indexName, config)` — `config` is a `CreateIndexRequest`
- `client.indexes.drop(tableName, indexName)`

### Users & Auth
- `client.users.getCurrentUser()` / `client.users.list()`
- `client.users.get(userName)` / `client.users.create(userName, request)` / `client.users.delete(userName)`
- `client.users.updatePassword(userName, newPassword)`
- `client.users.getPermissions(userName)` / `client.users.addPermission(userName, permission)` / `client.users.removePermission(userName, resource, resourceType)`

### Agents
- `client.retrievalAgent(request, callbacks?)` — retrieval pipeline / agentic retrieval
- `client.chatAgent(userMessage, config, history?, callbacks?)` — multi-turn wrapper that accumulates `ChatMessage[]`. It defaults `max_internal_iterations` to 5 (agentic, unlike the API's own default of 0) and sets `stream: !!callbacks`. The return is a union: `ChatAgentTurnResult` (`{ result, messages }`) without callbacks, `{ abortController, messages: Promise<ChatMessage[]> }` with them
- `client.queryBuilderAgent(request)` — natural language → structured query
- `client.evaluate(request)` — standalone LLM-as-judge evaluation

### Escape hatch
- `client.getRawClient()` — the underlying `openapi-fetch` client

## Retrieval Agent Streaming

```typescript
const result = await client.retrievalAgent(
  {
    query: 'how does raft work',
    queries: [{ table: 'docs', semantic_search: 'how does raft work', indexes: ['emb'], limit: 10 }],
    generator: { provider: 'openai', model: 'gpt-4o' },
    stream: true,
    steps: { generation: { enabled: true } }
  },
  {
    onClassification: (data) => {},
    onReasoning: (chunk) => {},
    onHit: (hit) => {},
    onGeneration: (chunk) => {},      // answer text arrives here
    onConfidence: (data) => {},
    onFollowup: (question) => {},
    onEvalResult: (data) => {},
    onFilterApplied: (filter) => {},
    onSearchExecuted: (data) => {},
    onStepStarted: (step) => {},
    onStepProgress: (data) => {},
    onStepCompleted: (step) => {},
    onDone: (result) => {},
    onError: (message) => {}          // string, not Error
  }
)

// Return type is RetrievalAgentResult | AbortController — narrow before aborting:
if (result instanceof AbortController) result.abort()
```

The response shape decides the branch: a JSON response resolves to `RetrievalAgentResult`, an SSE response resolves to an `AbortController` and drives the callbacks. Callbacks are only wired up for SSE.

## Key Types

All exported from `@antfly/sdk`:

- `QueryRequest`, `QueryResult`, `QueryHit`, `QueryResponses`, `QueryHitsTotal`, `QueryOptions`
- `AggregationRequest`, `AggregationBucket`, `AggregationResult`
- `Table`, `CreateTableRequest`, `TableSchema`, `BatchRequest`, `BatchResult`, `MultiBatchRequest`
- `IndexConfig`, `IndexType`, `IndexStatus`, `CreateIndexRequest`, `CreatedIndex`
- `User`, `Permission`, `ResourceType`, `CreateUserRequest`
- `RetrievalAgentRequest`, `RetrievalAgentResult`, `RetrievalAgentSteps`, `RetrievalAgentStreamCallbacks`
- `ChatAgentConfig`, `ChatAgentTurnResult`, `ChatMessage`, `ChatStreamCallbacks`, `ChatToolsConfig`
- `GeneratorConfig`, `GeneratorProvider`, `EmbedderConfig`, `RerankerConfig`, `EvalConfig`, `EvalResult`
- `AntflyConfig`, `AntflyAuth`, `AntflyError`

Not everything in the SDK's internal `types.ts` reaches the package root — `AntflyQuery`, `ScanKeysRequest`, `EvalRequest`, and the individual query shapes (`WildcardQuery`, `TermQuery`, …) are not re-exported. Reach them through the generated schema maps instead: `import type { components, query_components } from '@antfly/sdk'`, then `query_components['schemas']['WildcardQuery']`.

Value exports worth knowing: `generatorProviders`, `embedderProviders`, `formatQueryHitsTotal`, `queryResultHitsTotal`, `queryHitsTotalValue`, `queryHitsTotalIsExact`, `queryResultTotalHits`, `serializeEmbeddings` / `deserializeEmbeddings`, `InferenceClient`.

Typed error classes: `QueryTemporarilyUnavailableError` (with `QUERY_TEMPORARILY_UNAVAILABLE_CODES`), `StorageReadTemporarilyUnavailableError`, `StorageResourceExhaustedError`, `HierarchyCursorStaleError`, `InferenceAPIError`, `InferenceCapacityError`.

`generatorProviders` = `antfly`, `ollama`, `gemini`, `openai`, `anthropic`, `vertex`, `cohere`, `openrouter`. The API's `GeneratorProvider` enum also accepts `bedrock` and `mock`. Both are schema-only lists — the retrieval agent behind `/db/v1/agents/retrieval` executes only `gemini`, `vertex`, `openai`, `ollama`, and `antfly`, and 400s on the rest. `embedderProviders` = `antfly`, `ollama`, `gemini`, `vertex`, `openai`, `openrouter`, `bedrock`, `cohere`, `mock`.

### Query Builder Helpers

Typed constructors for Antfly queries:

`term`, `match`, `matchPhrase`, `prefix`, `fuzzy`, `queryString`, `numericRange`, `dateRange`, `matchAll`, `matchNone`, `boolean`, `conjunction`, `disjunction`, `docIds`, `geoDistance`, `geoBoundingBox`

```typescript
import { conjunction, match, term, type QueryRequest } from '@antfly/sdk'

const request: QueryRequest = {
  table: 'products',
  full_text_search: conjunction([
    match('laptop', 'title'),
    term('electronics', 'category')
  ]),
  limit: 10
}
```

`boolean({ must, should, mustNot, filter, boost, minShouldMatch })` builds the compound form; `disjunction(queries, min?)` sets the minimum-should-match. Note the exports are `conjunction`/`disjunction`, not `conjuncts`/`disjuncts` (those are the JSON field names the helpers emit). There is no `wildcard` helper — build `{ wildcard, field }` by hand.

## Sharp Edges

- **Errors are thrown, not returned.** Every method throws an `Error` on a failed response; wrap calls in try/catch instead of checking status codes. The one exception is `connections.list`, which returns `undefined` on a 404 so servers predating the endpoint degrade quietly
- `client.query()` returns `QueryResult | undefined` (first response only); `client.multiquery()` and `client.tables.query()` return `QueryResponses` with a `responses` array — different shapes
- `retrievalAgent()` returns `RetrievalAgentResult | AbortController`; narrow the union before calling `.abort()`
- Streaming callbacks are individually optional, but the answer text only arrives through `onGeneration` — `onDone` delivers the final `RetrievalAgentResult`
- `abort()` on the controller is the only way to stop a stream — there is no default timeout
- Typed error classes are narrow, not universal. `StorageResourceExhaustedError` (429, carrying `retryAfterSeconds`) comes only from `indexes.create`. The query paths — `query`, `multiquery`, `tables.query`, `tables.multiquery` — are the only source of `QueryTemporarilyUnavailableError` (503, also carrying `retryAfterSeconds`) and `HierarchyCursorStaleError` (409). `batch` / `multiBatch` / `linearMerge` throw a plain `Error` for every failure, 429 included. Catch the typed subclasses before generic `Error`, but do not expect them everywhere
- `tables.batch` / `multiBatch` / `linearMerge` enforce request and response size caps (`DEFAULT_WRITE_MAX_REQUEST_BYTES` / `DEFAULT_WRITE_MAX_RESPONSE_BYTES`). The request cap throws pre-flight, before any network call; the response cap throws post-flight, after an oversized body has already been read. Raise either through the `*WithOptions` variants: `tables.batchWithOptions`, `multiBatchWithOptions`, `linearMergeWithOptions`
