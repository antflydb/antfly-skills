# TypeScript SDK — `@antfly/sdk`

## Installation

```
npm install @antfly/sdk
```

ES module + CommonJS. Full TypeScript types included.

## Client Initialization

```typescript
import { AntflyClient } from '@antfly/sdk'

const client = new AntflyClient({
  baseUrl: '{{ANTFLY_API_URL}}',
  auth: { type: 'apiKey', keyId: '...', keySecret: '...' }
})
```

### Auth Options

| Type | Config |
|------|--------|
| API Key | `{ type: 'apiKey', keyId: string, keySecret: string }` |
| Bearer | `{ type: 'bearer', token: string }` |
| Basic | `{ username: string, password: string }` |

Backwards compatible: `client.setAuth(username, password)` also works.

## Methods

### Tables
- `client.tables.list()` — list all tables
- `client.tables.get(name)` — table details (schema, indexes, shards)
- `client.tables.create(name, config)` — create table with indexes, schema, shards
- `client.tables.drop(name)` — delete table
- `client.tables.batch(name, { inserts, deletes, transforms })` — document CRUD
- `client.tables.lookup(name, key)` — get document by key
- `client.tables.backup(name, config)` / `client.tables.restore(name, config)`

### Queries
- `client.query(request)` — single query (full-text, semantic, hybrid)
- `client.multiquery(requests)` — batch queries (NDJSON internally)
- `client.tables.query(name, request)` — table-scoped query

### Indexes
- `client.indexes.list(table)` / `client.indexes.get(table, name)`
- `client.indexes.create(table, name, config)` / `client.indexes.drop(table, name)`

### Users & Auth
- `client.users.get(name)` / `client.users.create(name, config)`
- `client.users.updatePassword(name, password)`
- `client.users.getPermissions(name)` / `client.users.addPermission(name, perm)` / `client.users.removePermission(name, resource, type)`

### Streaming (Retrieval Agent)
```typescript
const controller = await client.agents.retrieval(request, {
  onClassification: (data) => { },
  onReasoning: (chunk) => { },
  onHit: (hit) => { },
  onGeneration: (chunk) => { },
  onFollowup: (question) => { },
  onComplete: () => { }
})

// Cancel:
controller.abort()
```

Returns `AbortController`. Callbacks fire as SSE events arrive.

## Key Types

All exported from `@antfly/sdk`:

- `QueryRequest`, `QueryResult`, `QueryHit`, `QueryResponses`
- `AggregationBucket`, `AggregationResult`
- `Table`, `CreateTableRequest`, `TableSchema`
- `IndexConfig`, `IndexType`, `IndexStatus`
- `User`, `Permission`, `CreateUserRequest`
- `RetrievalAgentRequest`, `RetrievalAgentResult`

### Query Builder Helpers

Utility functions for constructing Bleve queries:

`term`, `match`, `matchPhrase`, `conjuncts`, `disjuncts`, `prefix`, `fuzzy`, `wildcard`, `numericRange`, `dateRange`

```typescript
import { conjuncts, term, match } from '@antfly/sdk'

const query = conjuncts([
  match('laptop', 'title'),
  term('electronics', 'category')
])
```

## Sharp Edges

- `client.query()` returns `QueryResult` for single query; `client.multiquery()` returns `QueryResponses` with a `responses` array — different shapes
- Streaming callbacks are optional individually, but you need at least `onGeneration` to get the answer text
- `abort()` on the controller is the only way to stop a streaming request — no timeout by default
- SDK uses `openapi-fetch` internally — lightweight, but errors surface as HTTP status codes, not exceptions by default
