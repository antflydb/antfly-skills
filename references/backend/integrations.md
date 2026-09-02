# Integrations — CDC, Object Storage, Document Sync

## CDC from PostgreSQL

Antfly has built-in change data capture that pulls INSERT/UPDATE/DELETE from PostgreSQL into an
Antfly table using logical replication. No external daemon.

**How it works**:
1. A source moves through a lifecycle: `snapshot` (backfill of existing rows through the normal batch-write path) → `cutover_prepared` (slot and publication established, consistent point recorded) → `streaming`, with intermediate and failure states persisted alongside them — `snapshot_complete` and `cutover_preparing` in between, `streaming_failed` and `failed` when a round classifies its error as terminal. Drive status checks off the recorded phase, not off the clean three-step reading
2. The slot and publication are created by Antfly, or reused if pre-created
3. Streaming **polls** the logical slot with `pg_logical_slot_peek_binary_changes(..., 'proto_version', '2', ...)`. There is no long-lived streaming replication connection
4. Metadata-owned coordinators drive every source on throttled ~1s leader rounds — there is no per-source worker and no exponential backoff, just flat rounds with each failure classified `retryable` or `terminal`
5. WAL changes are converted to Antfly transform operations and applied to the table
6. Snapshot offsets, `prepared_checkpoint`, and stream checkpoints are persisted in the metadata Raft store for crash recovery
7. Replicated rows go through the normal batch path, so enrichments (embeddings, summaries) apply exactly as they do for any other write

**Requirements**:
- PostgreSQL **14+** unconditionally — that is the floor for pgoutput protocol v2, which the poller requests. **15+** only when a source sets `publication_filter`, since Antfly then emits `CREATE PUBLICATION ... WHERE (...)` and publication row filters are a 15 feature
- `wal_level = logical` on the source database (server-wide, requires restart)
- A database user with the `REPLICATION` attribute (or the managed-service equivalent)

**Configuration**: CDC is declared **per table**, via `replication_sources[]` in the table
create/update body. A `cdc` connection *kind* does exist in node config and is reported read-only by
`GET /db/v1/connections?types=cdc`; what is absent is any create/update endpoint for it.

```json
{
  "replication_sources": [
    {
      "type": "postgres",
      "dsn": "${secret:pg.users_dsn}",
      "postgres_table": "users",
      "key_template": "id"
    }
  ]
}
```

| Field | Required | Notes |
|---|---|---|
| `type` | Yes | `"postgres"` |
| `dsn` | Yes | Connection string; supports `${secret:key}` |
| `postgres_table` | Yes | Source table in PostgreSQL |
| `key_template` | No | Antfly document key. Column name or `{{col}}` template. The spec documents a default of `"id"`; the implementation defaults to the row's `_id`, falling back to `id` |
| `slot_name` | No | Auto-derived. Set when using a pre-created slot |
| `publication_name` | No | Auto-derived. Set when using a pre-created publication |
| `on_update` | No | Transform ops for INSERT/UPDATE. Default passthrough |
| `on_delete` | No | Transform ops for DELETE. With `on_update` set, the default derives `$unset` from its `$set` paths; with neither set, the default unsets **every** replicated column on the deleted row, excluding the fields named by `key_template`. Use the `$delete_document` op to remove the document outright |
| `publication_filter` | No | Bleve-style filter translated to a SQL `WHERE` clause on the publication, so rows are filtered at the source. Applied **only when Antfly creates the publication**: if one by that name already exists it is left untouched, so changing or adding a filter later is a silent no-op until the publication is dropped and recreated |
| `routes` | No | Conditional fan-out: each route's `where` filter is evaluated per row and matches write to its `target_table`. When present, top-level `on_update`/`on_delete` are ignored |
| `require_exact_cutover` | No | Fail terminally rather than degrade to `slot_resumed` when an exported-snapshot exact cutover is unavailable |

`ReplicationSource` also carries `status` and `action_hint` members. Both are **response-only** — they appear in `GET` table detail responses and are not fields you set on a create/update body.

The Antfly schema is optional — passthrough mode `$set`s every PostgreSQL column onto the document.
`GET /db/v1/connections?types=cdc` reports replication status and is read-only.

**Use case**: Keep a searchable copy of Postgres data with semantic search and RAG capabilities,
without changing the source application.

See the CDC replication guide in the Antfly repository (`docs/guides/cdc-replication.mdx`) for
configuration details.

## Object Storage Engine

Object storage is a **storage engine** (`storage.engine: "object"`), available in `serverless`
deployment mode — not a per-table override. Serving state is generation-scoped: workers read
immutable published generations, with `artifacts`, `manifests`, `wal`, `progress`, and `catalog`
lanes in the object store.

The directory-backed `local` engine and single-file `lite` engine do not accept object-store fields.
Per `docs/s3-storage.md`, changing engines is an explicit backup/restore migration.

**Protocols**: the object storage engine accepts **only** `protocol: "s3"` — `validateStorageConnection`
rejects a connection with any other protocol. A `gcs` `external_io` connection exists and serves other
capabilities, but it cannot back `storage.engine: "object"`. (`antfly serverless` separately accepts
`gs://bucket/prefix` lane URIs passed directly via flags/env — that path bypasses the connection config.)
MinIO is the supported local-dev path.

**Configuration** — a named, capability-scoped connection plus a storage location:

```json
{
  "deployment_mode": "serverless",
  "connections": {
    "production-storage": {
      "kind": "external_io",
      "capabilities": ["storage.primary"],
      "external_io": {
        "protocol": "s3",
        "region": "us-west-2",
        "endpoint": "s3.amazonaws.com",
        "buckets": ["antfly-data", "antfly-wal"],
        "prefix": "production",
        "bucket_provisioning": "require_existing"
      }
    }
  },
  "storage": {
    "engine": "object",
    "object": {
      "connection": "production-storage",
      "bucket": "antfly-data",
      "prefix": "production/cluster-1",
      "lanes": {
        "wal": { "bucket": "antfly-wal", "prefix": "production/cluster-1/wal" }
      }
    }
  }
}
```

The root location supplies defaults; each lane can override `connection`, `bucket`, or `prefix`.
Locations sharing a connection share one object-store client and HTTP pool; a different connection is
an isolated credential and transport boundary. Bucket allowlists and prefix boundaries are validated
at startup and fail closed.

`bucket_provisioning: "create_if_missing"` exists for local dev and controlled test environments;
use `require_existing` in production and provision the bucket, encryption, versioning, and IAM policy
in infrastructure code.

**Credentials**: prefer `credentials.source` of `default` (the refreshable AWS chain: environment,
web identity/IRSA, shared profiles, ECS, EC2 metadata), `profile`, or `web_identity`. Static keys
(`source: "static"`) belong in a secret store and are referenced as
`${secret:storage.access_key_id}` / `${secret:storage.secret_access_key}`.

Keep primary-storage credentials separate from `remote_content.s3`, which only grants read access to
customer-provided objects for template helpers.

See `docs/s3-storage.md` in the Antfly repository for the setup guide, with two caveats where the
guide and the config parser disagree. The guide's static-credentials example puts `access_key_id` and
`secret_access_key` directly on `external_io`; the parser accepts only `protocol`, `endpoint`,
`region`, `addressing_style`, `bucket_provisioning`, `buckets`, `prefix`, `use_ssl`, and
`credentials` there, so those keys must nest under `credentials.{...}` or the config is rejected. The
guide's summary line also offers Google Cloud Storage; a `gcs` connection parses, but the object
storage engine validator requires `protocol: "s3"`.

## Document Sync (DocsAF)

Antfly includes document ingestion connectors for various sources:

| Source | Description | `docsaf` CLI |
|--------|-------------|--------------|
| Filesystem | Watch a directory, sync files into Antfly | `--source filesystem` (needs `--dir`) |
| Web Crawl | Crawl a website, index pages | Library only |
| Git | Index a git repository's contents | Library only |
| Google Drive | OAuth-based folder sync | `--source google-drive` (needs `--drive-folder`) |
| S3 | Import documents from S3-compatible object storage | Library only |

The `docsaf sync` CLI accepts only `filesystem` and `google-drive` for `--source`; anything else is
rejected with "unknown --source". The web, git, and S3 sources exist in the `docsaf` Go package and
are reachable by embedding it, not from the shipped command.

DocsAF uses LinearMerge internally: it pages records to `POST /db/v1/tables/{table}/merge` with a
`last_merged_id` cursor. The server sorts each page itself and range-deletes, per page, the Antfly
records in that key range that the page did not contain.

## Sharp Edges

- CDC requires Postgres `wal_level = logical` — server-level setting, not per-database, and requires a restart. Postgres must be 14+ (15+ if any source sets `publication_filter`) and the replication user needs the `REPLICATION` attribute.
- A replication slot retains WAL. If Antfly is down for an extended period, Postgres disk usage grows.
- Object storage and static credentials: never hardcode. Prefer `credentials.source` `default` / `profile` / `web_identity`; otherwise use `${secret:...}` references against the secret store.
- LinearMerge request bodies are capped at **64 MiB** — larger requests return HTTP 413. This is the global public-API body cap, not a merge-specific one.
- LinearMerge is not safe for concurrent operations with overlapping key ranges — it is a single-client sync API. Every key in a page must be greater than the `last_merged_id` you send with it.
- General guidance (not a measured figure): object storage reads cross the network, so a workload that was tuned against local NVMe should be re-benchmarked before assuming equivalent latency.
