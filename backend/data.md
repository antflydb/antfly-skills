# Data — Loading, Modifying, Deleting Documents

## Batch Operations

`POST /api/v1/{table}/batch`

The primary endpoint for document CRUD. Accepts a body with any combination of:

### Insert
`inserts` — map of document key → document body (JSON object).

```json
{
  "inserts": {
    "doc-1": { "title": "First", "content": "..." },
    "doc-2": { "title": "Second", "content": "..." }
  },
  "sync_level": "aknn"
}
```

Keys are strings. Documents are arbitrary JSON objects (conforming to schema if one exists).

### Delete
`deletes` — array of document keys to remove.

```json
{
  "deletes": ["doc-1", "doc-2"]
}
```

### Transform (In-Place Updates)
`transforms` — MongoDB-style atomic updates per document.

Operators:
| Op | Effect |
|----|--------|
| `$set` | Set field value |
| `$inc` | Increment numeric field |
| `$mul` | Multiply numeric field |
| `$push` | Append to array |
| `$pull` | Remove from array |
| `$min` | Set to minimum of current and given value |
| `$max` | Set to maximum of current and given value |
| `$unset` | Remove field |
| `$currentDate` | Set field to current timestamp |

```json
{
  "transforms": [{
    "key": "doc-1",
    "operations": [
      { "op": "$inc", "path": "view_count", "value": 1 },
      { "op": "$set", "path": "updated_at", "value": "2026-04-03T00:00:00Z" }
    ]
  }]
}
```

Response includes counts: `inserted`, `deleted`, `transformed`, `failed`.

## Linear Merge (Bulk Import)

`POST /api/v1/{table}/linear-merge`

Best for large imports and migrations. Accepts sorted records with cursor-based pagination.

```json
{
  "records": {
    "key-001": { "title": "..." },
    "key-002": { "title": "..." }
  },
  "last_merged_id": "",
  "sync_level": "aknn"
}
```

**How it works**:
1. Records must be sorted by key (ascending)
2. `last_merged_id` is a cursor — pass `""` for the first batch, then the `next_cursor` from the response for subsequent batches
3. After all batches, send a final request with empty records and the last cursor to clean up orphaned documents (records that exist in Antfly but weren't in the import)

Response: `{ upserted, deleted, next_cursor }`

## Lookup

`GET /api/v1/{table}/keys/{key}` — fetch a document by key.

**Field projection**: `?fields=title,author` to limit returned fields. Supports:
- Nested paths: `user.address.city`
- Exclusions: `-_chunks.*._embedding` (prefix with `-`)
- Special fields: `_embeddings` for raw vectors

## Transactions

`POST /api/v1/transaction` — multi-table atomic batch.

```json
{
  "tables": {
    "users": { "inserts": { "user1": { ... } } },
    "orders": { "inserts": { "order1": { ... } } }
  }
}
```

Returns `{ status: "committed" }` or `{ status: "aborted", conflict: { ... } }`. Uses optimistic concurrency control.

## Sync Levels

Controls how much work completes before the write returns:

| Level | Waits for | Speed | Use when |
|-------|-----------|-------|----------|
| `propose` | Raft proposal | Fastest | Fire-and-forget writes |
| `write` | Pebble KV write | Fast | Need durability |
| `full_text` | Full-text index WAL | Medium | Need immediate full-text search |
| `enrichments` | Pre-compute enrichments | Slow | Need enrichments before commit |
| `aknn` | Vector index write | Slowest | Need immediate vector search |

Default is `propose`.

## Sharp Edges

- Linear merge **requires sorted keys** — unsorted input produces incorrect results
- Linear merge cursor-based: must track `next_cursor` between batches and do a final empty-records call to clean up orphans
- `sync_level: "aknn"` is significantly slower but necessary if you query immediately after write
- Transforms are atomic **per document**, not per batch — partial batch failures are possible
- Document keys are strings — numeric IDs must be string-encoded
- Batch endpoint can mix inserts, deletes, and transforms in a single request
