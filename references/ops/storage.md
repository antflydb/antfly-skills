# Storage — Lite, Local, Object

Deployment topology and durable storage are independent choices. A deployment mode answers *which processes run*; a storage engine answers *where durable state lives*.

| Engine | Durable representation | Typical mode |
|--------|------------------------|--------------|
| `lite` | One portable `.aflite` file, one writable owner | embedded, standalone |
| `local` | Directory-backed local shard and metadata storage | standalone, distributed |
| `object` | Object-store-backed durable data | serverless |

That table is the **process** engine. Separately, standalone and distributed processes support a per-table `storage.engine: local | object` setting: `object` tables keep the native catalog but store data as shared durable objects and allocate no data Raft replicas (owned-object lookups need `consistency=stale`). Changing a table's engine requires an explicit migration into a new table.

Storage is a tagged union: `storage.engine` is required, and the member matching it is required as well — `engine: local` without a `local` block is rejected, as is any non-matching member. Mixed local/object configurations are rejected so data placement cannot silently diverge.

## Local Engine

Directory-backed under `--data-dir`. The default primary backend is LSM, and shard data, the metadata Raft apply store, full-text, dense/HBC, sparse, and graph-reverse storage all sit on it. LMDB survives only as a legacy primary-backend variant: it is compiled out of the shipped `antfly` binary and no config key or CLI flag selects it, so nothing in a released build stores data in LMDB. Even in an LMDB build only the primary document store would follow it — the index subsystems resolve to LSM for every primary kind.

```json
{
  "storage": {
    "engine": "local",
    "local": { "base_dir": "antflydb" }
  }
}
```

`base_dir` has schema default `"antflydb"`, but when the key is unset the runtime resolves `$HOME/.antfly` and only falls back to `antflydb` when `HOME` is empty or unset. See `standalone.md` for the data-directory layout.

## Lite Engine

```json
{
  "storage": {
    "engine": "lite",
    "lite": { "path": "./data.antfly.aflite", "fsync": true }
  }
}
```

`path` must end in `.aflite`. Lite pins `replication_factor: 1`, `default_shards_per_table: 1`, and `disable_shard_alloc: true`, and rejects non-empty `metadata.orchestration_urls` / `raft_urls`. The CLI equivalent is `antfly standalone --storage-engine lite --storage-path <f.aflite> [--fsync <bool>]`; see `standalone.md` for adoption limits.

## Object Engine (Serverless)

The object engine backs serverless mode: stateless workers over immutable object-store state, split into `artifacts`, `manifests`, `wal`, `progress`, and `catalog` lanes. As a process engine it requires `deployment_mode: serverless` — any other mode is rejected at config load. Serverless itself is still **unreleased** upstream (control-plane auth/quota and job tracking are open).

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
        "use_ssl": true,
        "buckets": ["antfly-data", "antfly-wal"],
        "prefix": "production",
        "bucket_provisioning": "require_existing",
        "credentials": {
          "source": "web_identity",
          "role_arn": "arn:aws:iam::123456789012:role/antfly-data",
          "token_file": "/var/run/secrets/data/token"
        }
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

- `connection` must name an `external_io` connection with `protocol: s3` or `protocol: gcs` and the `storage.primary` capability
- `buckets` is a required non-empty allowlist — unrestricted bucket access is never inferred
- `bucket_provisioning`: `require_existing` (default) or `create_if_missing`
- Each lane may override `connection`, `bucket`, or `prefix`; lanes on the same connection share one client and connection pool
- S3 `credentials.source`: `default` | `static` | `profile` | `web_identity`. GCS `credentials.source`: `default` | `bearer_token` | `service_account` (GCS connections also take `project_id`)

S3 `default` uses the refreshable AWS default chain (environment, web identity/IRSA, shared profiles, ECS task credentials, EC2 instance metadata). GCS `default` checks `GOOGLE_APPLICATION_CREDENTIALS`, the gcloud ADC file, then the GCE/GKE metadata server. Static keys should come from secret references, never plaintext.

### Compatible Services

S3-compatible object stores (AWS S3, Cloudflare R2, MinIO) via `protocol: s3`, and Google Cloud Storage via `protocol: gcs`. With `--config`, serverless derives each lane URI from the selected connection — `s3://bucket/prefix/...` or `gs://bucket/prefix/...`.

The alternative is URI configuration without a connection-based config: `antfly serverless` accepts `file://`, `s3://`, and `gs://` lane URIs as flags or environment variables (`--wal-uri gs://bucket/prefix`, `ANTFLY_SERVERLESS_WAL_URI`, …). Mixing URI overrides with a connection-based config is rejected.

## Native Artifacts and Lake Cache

- `storage.artifacts` (`connection`, `bucket`, optional `prefix`) is an optional object-storage location for native artifacts such as lake search indexes, accepted alongside any process engine. The connection needs the `storage.primary` capability; the bucket must be in its `buckets` allowlist and the prefix inside its `prefix` scope.
- `lake_cache` (top-level) is a disposable node-local cache for versioned Parquet/Iceberg reads: `enabled` (default `true`), `root` (default `cache/lake-ranges` under local storage, or the Lite file's directory), `max_memory_bytes` (64 MiB), `max_disk_bytes` (10 GiB), `max_entries` (16384), `max_write_queue_bytes` (32 MiB), `max_write_queue_entries` (16), `protected_bytes` (256 MiB; 0 disables). Unknown keys and zero limits (except `protected_bytes`) are rejected.

## Local MinIO Development

`devops/docker-compose-s3` runs MinIO plus a locally built Antfly image on `serverless combined --host 0.0.0.0 --health-port 4200`, with ports published on host `127.0.0.1` — see `docker.md`:

```bash
cd devops/docker-compose-s3 && docker compose up -d
```

- MinIO on `9000` (API) and `9001` (console), credentials `minioadmin` / `minioadmin`, passed to Antfly as `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` (default credential chain)
- Bucket `antfly-data` created on startup by the `minio-setup` job
- Endpoint `minio:9000`, `use_ssl: false`, `addressing_style: path`

## Sharp Edges

- Process-level `storage.engine: object` outside `deployment_mode: serverless` is a config error, not a fallback
- Changing engines is an explicit backup/restore migration, not a live toggle
- The bucket allowlist and prefix boundaries are node config — rotating a credential cannot widen them
- Low-level URI flags/env overrides are supported only *without* a connection-based config; mixing the two is rejected
- Credential references are re-resolved before each backup, restore, or probe, so rotation applies without a restart — but primary object clients resolve once during serverless bootstrap, so use `default`, `profile`, or `web_identity` there
- `remote_content.s3.*` is a separate trust domain from `storage.primary` — do not share a writer credential with it
