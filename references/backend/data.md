# Data — Loading, Modifying, Deleting Documents

## Batch Operations

`POST /db/v1/tables/{tableName}/batch`

The primary endpoint for document CRUD. Accepts any combination of:

### Insert
`inserts` — map of document key → document body (JSON object). Inserts are upserts.

```json
{
  "inserts": {
    "doc-1": { "title": "First", "content": "..." },
    "doc-2": { "title": "Second", "content": "..." }
  },
  "sync_level": "full_index"
}
```

Keys are strings. Documents are arbitrary JSON objects (conforming to the schema if one exists).

### Delete
`deletes` — array of document keys to remove. Non-existent keys are silently ignored. Within one batch the server coalesces writes first and then applies deletes over them, so a key present in both `inserts` and `deletes` ends up **deleted**. (The OpenAPI prose saying deletions are processed before inserts is stale.)

```json
{
  "deletes": ["doc-1", "doc-2"]
}
```

### Transform (In-Place Updates)
`transforms` — MongoDB-style atomic updates, applied at the storage layer so there is no read-modify-write race.

Operators:
| Op | Effect |
|----|--------|
| `$set` | Set field value |
| `$setOnInsert` | Set only when the document is being created |
| `$unset` | Remove field (no `value` needed) |
| `$inc` | Increment numeric field |
| `$push` | Append to array |
| `$addToSet` | Append to array only if absent |
| `$min` | Set to minimum of current and given value |
| `$max` | Set to maximum of current and given value |

`path` is a JSONPath (`"$.views"`, `"$.user.name"`; a bare `"user.name"` also works). Each transform takes `key`, `operations` (applied in sequence), and an optional `upsert` flag that creates the document when it does not exist.

```json
{
  "transforms": [{
    "key": "article:123",
    "upsert": true,
    "operations": [
      { "op": "$inc", "path": "$.views", "value": 1 },
      { "op": "$set", "path": "$.lastViewed", "value": "2026-07-28T12:00:00Z" }
    ]
  }]
}
```

**Transform results are not validated against the table schema.** That is what makes them fast, and it means invalid documents are possible — keep operations schema-compliant yourself.

### Response

`BatchResponse` is `{ status, inserted, deleted, transformed }`. `status` is one of:

| Status | Meaning |
|--------|---------|
| `committed` | Durable and visible |
| `committed_pending` | Committed; requested visibility or participant propagation still completing |
| `committed_repair_required` | Primary write committed, but a terminal enrichment failure needs operator repair |

There is no `failed` count — a batch either commits or errors.

**Batches are atomic.** Within a shard, operations commit atomically; when a batch spans shards, Antfly runs distributed 2PC, so all writes succeed or none do.

## Linear Merge (Bulk Import)

`POST /db/v1/tables/{tableName}/merge`

Best for large imports and keeping Antfly in sync with an external sorted source. It performs a three-way merge over a key range: upsert what you send, delete Antfly keys in the range that you did not.

```json
{
  "records": {
    "product:001": { "name": "Laptop" },
    "product:002": { "name": "Mouse" }
  },
  "last_merged_id": "",
  "sync_level": "write"
}
```

**How it works**:
1. The server sorts the records itself — you do not have to send them in order. The real constraint is that **every key must sort strictly after `last_merged_id`**; otherwise the request is rejected with 400.
2. `last_merged_id` is the cursor: `""` for the first page, then `next_cursor` from the previous response.
3. After the last page of data, send a final request with `"records": {}` **and** `last_merged_id` set to the final cursor, to sweep orphaned documents past that point. Empty records with no cursor is rejected.

`dry_run: true` reports what would be deleted (`deleted_ids`) without changing anything. The server does **not** decompress request bodies — send plain JSON. Bodies over 64 MiB return 413; that cap is the global public-API request body limit, not merge-specific.

Response: `{ status, upserted, deleted, skipped, next_cursor, key_range, keys_scanned }`, plus `deleted_ids` and `message` when `dry_run` is set. `took` and `failed` are declared in the spec but never emitted. `partial` and `error` are declared statuses, but the current server always returns `success`.

Merge defaults to `sync_level: "write"` — unlike batch, which defaults to `propose`. Merges are not safe to run concurrently over overlapping key ranges.

## Lookup

`GET /db/v1/tables/{tableName}/documents/{key}` — fetch a document by key.

**Field projection**: `?fields=title,author`. Supports:
- Nested paths: `user.address.city`
- Wildcards: `_chunks.*`
- Exclusions: `-_chunks.*._embedding` (prefix with `-`)
- Special fields: `_embeddings`, `_chunks`, `_summaries`

**Consistency**: `?consistency=read_index` (default, linearizable via the primary), `leader_lease`, or `stale` (a hot standby serves at its safe-read LSN).

A 200 response carries an `X-Antfly-Version` header — the version token for that document. A missing key is a **404** with no such header. `"0"` is the value the *client* supplies in an OCC `read_set` to assert the key did not exist, but the server does not honor that assertion (see below) — capture the header and build `read_set` entries only from keys that exist.

## Transactions

**Cross-table atomic batch**: `POST /db/v1/batch`

```json
{
  "tables": {
    "users": { "inserts": { "user:123": { "name": "John" } } },
    "orders": { "inserts": { "order:456": { "user_id": "user:123" } } }
  }
}
```

All operations across all tables commit atomically via 2PC.

**OCC transaction**: `POST /db/v1/transactions/commit`. Stateless — there is no begin step. `read_set` is **required**: an array of `{table, key, version}` using the `X-Antfly-Version` values captured at read time. `tables` carries the write set in the same shape as `/db/v1/batch`.

`"0"` is documented as an assert-absent sentinel, but it does not work on the shipped server. The API pre-check walks `read_set` and reports a conflict the moment a lookup misses, with no exemption for a zero version — so a `read_set` entry for an absent key **always** aborts with 409, whatever version you send. The 0-means-absent rule lives only in the storage layer, which the pre-check short-circuits. Insert-if-absent through the documented `read_set` flow is therefore not available; guard on an existing key's version instead.

```json
{
  "read_set": [{ "table": "accounts", "key": "acct:1", "version": "42" }],
  "tables": { "accounts": { "inserts": { "acct:1": { "balance": 90 } } } }
}
```

If any version has changed, the commit is aborted with 409 and a `conflict` object naming the offending key.

**Stateful sessions**: `POST /db/v1/transactions/begin`, then `/db/v1/transactions/{id}/read|write|delete|stage|savepoints|commit|abort` for server-managed read-modify-write.

Commit response `status` is one of `committed`, `committed_visibility_pending`, `committed_recovery_pending`, `committed_repair_required`, `aborted`.

## Sync Levels

Controls how much work completes before the write returns:

| Level | Waits for | Speed | Use when |
|-------|-----------|-------|----------|
| `propose` | Raft proposal | Fastest | Fire-and-forget writes |
| `write` | Local KV/LSM write | Fast | Need durability |
| `full_text` | Full-text index WAL | Medium | Need immediate full-text search |
| `enrichments` | Pre-computed enrichments | Slow | Need enrichments before commit |
| `full_index` | All index writes, vectors included | Slowest | Need immediate vector search |

Batch default is `propose`; merge default is `write`.

## Sharp Edges

- `sync_level: "aknn"` no longer exists — it is a removed alias and servers reject it. Use `full_index`.
- Linear merge does **not** require pre-sorted input, but every key must sort strictly after `last_merged_id` — otherwise 400.
- Linear merge needs the final `records: {}` + `last_merged_id` call to delete orphans; an empty body with no cursor is rejected.
- Request bodies are capped at 64 MiB globally → 413 over that; the server does not decompress gzip request bodies.
- Transforms bypass schema validation — an operation can produce a document the schema would have rejected.
- Batches are atomic, single-shard and cross-shard alike; a `committed_pending` status means durable-but-still-propagating, not partially applied.
- Document keys are strings — numeric IDs must be string-encoded.
- A batch can mix inserts, deletes, and transforms in a single request; deletes win over an insert of the same key.
