# TypeScript SDK — `@antfly/sdk`

## Installation

```
npm install @antfly/sdk
```

Version `0.3.0`. ES module + CommonJS, full TypeScript types, `engines.node >= 24`. Runtime dependencies: `lossless-json`, `openapi-fetch`, `postgres-array`. `kysely` is an optional peer dependency, needed only for the `@antfly/sdk/kysely` subpath.

Entry points:

- `@antfly/sdk` — `AntflyClient`, `Client`, `InferenceClient`, query helpers, types
- `@antfly/sdk/sources` — `SourcesClient` / `StandaloneSourcesClient` (`new SourcesClient({ baseUrl, token, fetch? })`), `SourceServiceError`, and the source/run types
- `@antfly/sdk/kysely` — Kysely over Antfly's Postgres wire: `AntflyPostgresDialect`, `createAntflyPostgres` (you pass in the `pg` module), `createAntflyIntrospector`, `generateKyselyTypes`, `antflySearch`, `prepareKyselyMigrationTables`, `AntflyPersistentMigrationLock`

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

`SDKConfig` also takes `inferenceMaxBinaryResponseBytes`. The inference reranker method is still `InferenceClient.rerank(model, query, documents, options?)`.

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
- `client.tables.get(tableName, scope?)` — schema, indexes, shards; `scope` is `{ database, namespace }`
- `client.tables.create(tableName, config?)` — `config` is a `CreateTableRequest` (`num_shards`, `schema`, indexes …). Returns `Table | CommittedMutationOutcome`
- `client.tables.drop(tableName)` — returns `true | CommittedMutationOutcome`
- `client.tables.replaceSchema(tableName, schema, options?)` — full replacement
- `client.tables.patchSchema(tableName, patch, options?)` — RFC 7396 JSON Merge Patch (`null` removes a member)
- `client.tables.updateSchema(...)` — deprecated alias of `replaceSchema`
- `client.tables.batch(tableName, { inserts?, deletes?, transforms?, sync_level? })`
- `client.tables.batchWithOptions(tableName, request, { maxRequestBytes?, maxResponseBytes?, signal? })`
- `client.tables.lookup(tableName, key, { fields? })` — `fields` here is a comma-separated **string** (`"title,author,metadata.tags"`), not an array like everywhere else
- `client.tables.scan(tableName, request?)` — async generator over NDJSON documents
- `client.tables.scanAll(tableName, request?)` — same, collected into an array
- `client.tables.backup(tableName, request)` / `client.tables.restore(tableName, request, { idempotencyKey? })`
- `client.tables.artifacts.*` — generated-artifact enrichments and reprocess jobs
- `client.tables.rows.queryRaw/mutate`, `client.tables.constraints.status/retry/retire/repair` — relational rows and constraints
- `client.multiBatch({ tables, sync_level? })` — atomic cross-table batch
- `client.linearMerge(tableName, request)`
- `client.restoreJobs.startCluster/get/list/listAll/cancel`

Schema mutations take `{ expectedVersion?, rewrite?, idempotencyKey? }` and return `Table | CommittedMutationOutcome | RestoreJob` (`rewrite: true` builds a fresh generation through a restore job).

`CommittedMutationOutcome` is `{ status }`, one of `committed_visibility_pending`, `committed_superseded`, `committed_repair_required`, `committed_repair_unavailable`. The mutation **has committed**: read the resource to observe it instead of retrying. Check for it before treating a `create`/`drop`/schema result as a `Table` or `true`.

### Queries
- `client.query(request, { signal? })` — returns the **first** `QueryResult`
- `client.multiquery(requests)` — returns `QueryResponses` (NDJSON internally)
- `client.tables.query(tableName, request, { signal? })` — table-scoped, returns `QueryResponses`
- `client.tables.multiquery(tableName, requests)`
- `readAfterWrite(receipt, waitMs = 5000)` — turns an ingestion `ReadReceipt` into the `read_requirements` value for a query or SQL request

### Indexes
- `client.indexes.list(tableName, scope?)` / `client.indexes.get(tableName, indexName)`
- `client.indexes.create(tableName, indexName, config)` — `config` is a `CreateIndexRequest`
- `client.indexes.drop(tableName, indexName)`
- `client.indexes.retry(tableName, indexName, request, { signal? })` / `client.indexes.repair(...)` — index maintenance (`IndexMaintenanceRequest` → `IndexMaintenanceResponse`)

### Users & Auth
- `client.users.getCurrentUser()` / `client.users.list()`
- `client.users.get(userName)` / `client.users.create(userName, request)` / `client.users.delete(userName)`
- `client.users.updatePassword(userName, newPassword)`
- `client.users.getPermissions(userName)` / `client.users.addPermission(userName, permission)` / `client.users.removePermission(userName, resource, resourceType)`

### Agents
- `client.retrievalAgent(request, undefined?, { signal? }?)` — forces `stream: false`, resolves to `RetrievalAgentResult`
- `client.streamRetrievalAgent(request, callbacks, { signal? }?)` — forces `stream: true`, resolves to an `AbortController`; a JSON reply is routed into `onDone`. The `retrievalAgent(request, callbacks)` overload still works but is deprecated in its favour
- `client.chatAgent(userMessage, config, history?, callbacks?)` — multi-turn wrapper that accumulates `ChatMessage[]`. It defaults `max_internal_iterations` to 5 (agentic, unlike the API's own default of 0) and sets `stream: !!callbacks`. The return is a union: `ChatAgentTurnResult` (`{ result, messages }`) without callbacks, `{ abortController, messages: Promise<ChatMessage[]> }` with them
- `client.researchAgent(request, { signal? }?)` / `client.streamResearchAgent(request, callbacks, { signal? }?)` — deep-research agent (`ResearchAgentRequest`: `query`, `queries` required)
- `client.queryBuilderAgent(request)` — natural language → structured query
- `client.evaluate(request)` — standalone LLM-as-judge evaluation

### Other Surface

| Area | Methods |
|------|---------|
| Durable research jobs | `startResearchJob(request)`, `getResearchJob(id)`, `advanceResearchJob(id, { max_phases }?)`, `cancelResearchJob(id)`, `runResearchJob(request, { maxPhasesPerAdvance?, onJob?, signal? })` — start + advance to a terminal state |
| SQL | `executeSQL(request, options?)`, `prepareSQL` / `executePreparedSQL(id, request?)` / `closePreparedSQL(id)`, `openSQLConnection` / `closeSQLConnection(id)`, `getSQLTransactionOutcome(transactionId)` |
| Time series | `client.writeSeries(table, timestamp, readings, { batchSize?, syncLevel?, onBatch? })` (sequential batches; a failure stops the import, earlier batches stay committed), `client.series(options)` → `{ series, result }`, `client.latestSeries(...)`; standalone builders `timeSeriesTable`, `seriesQuery`, `seriesRead`, `seriesBatch`, `seriesSQL`, `seriesResults` |
| Graphs | `client.graphs.list/get/create/update/drop/execute/writeStatus` — `create`/`update` may return `CommittedMutationOutcome` |
| Memory | `client.memory.*` — `create`, `remember`, `recall`, `brief`, `consolidate`, `list`, `get`, `history`, `correct`, `forget`, … (`parseMemoryJSON` / `stringifyMemoryJSON` for lossless JSON) |
| Privacy | `client.privacy.get/put/preview/startScan/getScan/findings(table, …)` |
| Inference gateway | `client.inference.models()` / `client.inference.invoke(operation, body)` |

### Escape hatch
- `client.getRawClient()` — the underlying `openapi-fetch` client

## Retrieval Agent Streaming

```typescript
const controller = await client.streamRetrievalAgent(
  {
    query: 'how does raft work',
    queries: [{ table: 'docs', semantic_search: 'how does raft work', indexes: ['emb'], limit: 10 }],
    generator: { provider: 'openai', model: 'gpt-4o' },
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
    onToolMode: (mode) => {},
    onContextManagement: (event) => {},
    onStepStarted: (step) => {},
    onStepProgress: (data) => {},
    onStepCompleted: (step) => {},
    onDone: (result) => {},
    onErrorDetail: (error) => {},     // Error
    onError: (message) => {}          // string
  }
)

controller.abort()
```

An HTTP error status rejects the returned promise; errors after the stream opens go to `onErrorDetail` then `onError`, and an aborted stream reports neither. `onConfidence` also fires from the `done` payload when it carries `generation_confidence` and `context_relevance`.

## Key Types

All exported from `@antfly/sdk`:

- `QueryRequest`, `QueryResult`, `QueryHit`, `QueryResponses`, `QueryHitsTotal`, `QueryOptions`, `ReadReceipt`, `ReadRequirements`
- `AggregationRequest`, `AggregationBucket`, `AggregationResult`
- `Table`, `CreateTableRequest`, `TableSchema`, `BatchRequest`, `BatchResult`, `MultiBatchRequest`, `WriteOptions`, `SchemaMutationOptions`
- `IndexConfig`, `IndexType`, `IndexStatus`, `CreateIndexRequest`, `CreatedIndex`
- `User`, `Permission`, `ResourceType`, `CreateUserRequest`
- `RetrievalAgentRequest`, `RetrievalAgentResult`, `RetrievalAgentSteps`, `RetrievalAgentStreamCallbacks`, `SSEToolMode`, `AgentContextEvent`
- `ResearchAgentRequest`, `ResearchAgentResult`, `ResearchAgentStreamCallbacks`, `ResearchJob`, `ResearchReport`, `ResearchEvidence`
- `ChatAgentConfig`, `ChatAgentTurnResult`, `ChatMessage`, `ChatStreamCallbacks`, `ChatToolsConfig`
- `SQLRequest`, `SQLResponse`, `GraphQueryRequest`, `GraphQueryResult`, `SeriesQueryOptions`, `TimeSeries`
- `GeneratorConfig`, `GeneratorProvider`, `EmbedderConfig`, `RerankerConfig`, `EvalConfig`, `EvalResult`
- `AntflyConfig`, `AntflyAuth`, `AntflyError`

Not everything in the SDK's internal `types.ts` reaches the package root — `CommittedMutationOutcome`, `AntflyQuery`, `ScanKeysRequest`, `EvalRequest`, and the individual query shapes (`WildcardQuery`, `TermQuery`, …) are not re-exported. Reach them through the generated schema maps instead: `import type { components, query_components } from '@antfly/sdk'`, then `components['schemas']['CommittedMutationOutcome']` or `query_components['schemas']['WildcardQuery']`.

Value exports worth knowing: `generatorProviders`, `embedderProviders`, `indexEmbedderProviders`, `formatQueryHitsTotal`, `queryResultHitsTotal`, `queryHitsTotalValue`, `queryHitsTotalIsExact`, `queryResultTotalHits`, `readAfterWrite`, `InferenceClient`, and the numeric embedding codec `decodeNumericDenseFrame` / `serializeNumericDenseFrame` / `NUMERIC_RESPONSE_ACCEPT` / `NUMERIC_RESPONSE_MEDIA_TYPE` (`application/vnd.antfly.numeric.v1`). `serializeEmbeddings` / `deserializeEmbeddings` no longer exist.

`generatorProviders` = `cloudflare`, `anthropic`, `antfly`, `bedrock`, `apple`, `gemini`, `ollama`, `openai`, `chatgpt`, `openrouter`, `vertex` — the same set as the API's `GeneratorProvider` enum; `cohere` and `mock` are gone. Which of these the retrieval agent can run is a server question — see `../backend/rag.md`. `embedderProviders` = `cloudflare`, `antfly`, `bedrock`, `cohere`, `gemini`, `ollama`, `openai`, `openrouter`, `vertex`; `indexEmbedderProviders` is the subset usable for index embedders: `cloudflare`, `antfly`, `bedrock`, `ollama`, `openai`, `openrouter`.

### Error Classes

| Class | Thrown by | Carries |
|-------|-----------|---------|
| `AntflyHTTPError` | `tables.batch` / `multiBatch` / `linearMerge` (and `*WithOptions`), `tables.get`, `tables.lookup`, `indexes.get`, `tables.create` / `indexes.create` / `tables.restore` when not a typed case, SQL calls without a SQL diagnostic, privacy calls | `status`, `body`, `retryAfterSeconds`, `mutationOutcome` (`"unknown"` = the mutation may have applied; reconcile before retrying) |
| `AntflyResponseError` | a success response that is unusable (e.g. a batch reply with no outcome, an invalid privacy body) — reconcile before retrying | message only |
| `IndexMutationTemporarilyUnavailableError` | `tables.create`, `indexes.create`, `tables.restore` — 503 with a code in `INDEX_MUTATION_TEMPORARILY_UNAVAILABLE_CODES` | `code`, `retryAfterSeconds`, `retryable: true` |
| `StorageResourceExhaustedError` | `indexes.create` — 429 | `retryAfterMs`, `retryAfterSeconds` |
| `QueryTemporarilyUnavailableError` (`StorageReadTemporarilyUnavailableError` subclass) | query paths and agents — 503 with a code in `QUERY_TEMPORARILY_UNAVAILABLE_CODES` | `code`, `retryAfterSeconds` |
| `HierarchyCursorStaleError` | query paths and agents — 409 | `action: "restart_hierarchy_traversal"` |
| `InferenceCapacityError` | query paths and agents — 503 transient capacity; `InferenceClient` | |
| `SQLExecutionError` / `GraphExecutionError` | SQL calls whose error body is a SQL diagnostic / `graphs.execute` | `status`, `diagnostic` |
| `ResearchJobAdvanceConflictError` | `advanceResearchJob` — 409, another caller holds the lease | `retryAfterSeconds` |
| `InferenceTransportError` | `InferenceClient` network failures | `code`, `retryable: true` |
| `InferenceAPIError` | `InferenceClient` HTTP errors | |
| `ChatGPTConnectionError` | `client.chatgpt.*` | `status`, `code` |

"Query paths and agents" = `query`, `multiquery`, `tables.query`, `tables.multiquery`, plus `retrievalAgent`, `streamRetrievalAgent`, `researchAgent`, `streamResearchAgent`, and `queryBuilderAgent` (for the HTTP status of the initial request). Anything else is a plain `Error`.

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

- **Errors are thrown, not returned.** Every method throws on a failed response; wrap calls in try/catch instead of checking status codes. The one exception is `connections.list`, which returns `undefined` on a 404 so servers predating the endpoint degrade quietly
- `client.query()` returns `QueryResult | undefined` (first response only); `client.multiquery()` and `client.tables.query()` return `QueryResponses` with a `responses` array — different shapes
- Use `retrievalAgent(request)` for one JSON result and `streamRetrievalAgent(request, callbacks)` for SSE — no union narrowing needed. The SDK sets `stream` itself in both
- Streaming callbacks are individually optional, but the answer text only arrives through `onGeneration` — `onDone` delivers the final `RetrievalAgentResult`
- `abort()` on the controller (or the `signal` option) is the only way to stop a stream — there is no default timeout
- Mutations can commit without returning the resource: `tables.create`, `tables.drop`, schema mutations, and `graphs.create/update` may return a `CommittedMutationOutcome`, and an `AntflyHTTPError` with `mutationOutcome: "unknown"` or an `AntflyResponseError` means the write may have applied. Read state back before retrying. In 0.3.0 the batch paths build `AntflyHTTPError` without response headers, so `retryAfterSeconds` and `mutationOutcome` stay `undefined` there
- `tables.batch` / `multiBatch` / `linearMerge` enforce request and response size caps (`DEFAULT_WRITE_MAX_REQUEST_BYTES` / `DEFAULT_WRITE_MAX_RESPONSE_BYTES`). The request cap throws pre-flight, before any network call; the response cap throws after the request was sent, so the write may already have applied. Raise either through the `*WithOptions` variants: `tables.batchWithOptions`, `multiBatchWithOptions`, `linearMergeWithOptions`
