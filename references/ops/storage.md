# Storage — Lite, Local, Object

Deployment topology and durable storage are independent choices. A deployment mode answers *which processes run*; a storage engine answers *where durable state lives*.

| Engine | Durable representation | Typical mode |
|--------|------------------------|--------------|
| `lite` | One portable `.aflite` file, one writable owner | embedded, standalone |
| `local` | Directory-backed local shard and metadata storage | standalone, distributed |
| `object` | Object-store-backed durable data | serverless |

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

`path` must end in `.aflite`. Lite pins `replication_factor: 1`, `default_shards_per_table: 1`, and `disable_shard_alloc: true`.

## Object Engine (Serverless)

The object engine backs serverless mode: stateless workers over immutable object-store state, split into `artifacts`, `manifests`, `wal`, `progress`, and `catalog` lanes. It requires `deployment_mode: serverless` — any other mode is rejected at config load.

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

- `connection` must name an `external_io` connection with the `storage.primary` capability
- `buckets` is a required non-empty allowlist — unrestricted bucket access is never inferred
- `bucket_provisioning`: `require_existing` (default) or `create_if_missing`
- Each lane may override `connection`, `bucket`, or `prefix`; lanes on the same connection share one client and connection pool
- `credentials.source`: `default` | `static` | `profile` | `web_identity`

`default` uses the refreshable AWS default chain (environment, web identity/IRSA, shared profiles, ECS task credentials, EC2 instance metadata). Static keys should come from secret references, never plaintext.

### Compatible Services

S3-compatible object stores (AWS S3, Cloudflare R2, MinIO) via `protocol: s3`. `storage.engine: object` validation requires `protocol: s3`, so a `gcs` connection cannot back primary storage — GCS `external_io` connections exist for other capabilities.

GCS is reachable on the other path. `antfly serverless` parses lane URIs directly and accepts exactly three schemes — `file://`, `s3://`, and `gs://` — supplied as flags or environment variables (`--wal-uri gs://bucket/prefix`, `ANTFLY_SERVERLESS_WAL_URI`, and so on), with GCS credentials taken from the environment. The two paths are mutually exclusive: `--config` requires `storage.engine: object` and then rewrites every lane URI as an `s3://` string. A GCS serverless deployment is therefore URI-configured, not config-configured.

## Local MinIO Development

`devops/docker-compose-s3` runs MinIO plus a locally built Antfly image on `serverless combined`. As shipped, the Antfly container's own published ports do not answer — see `docker.md` for what to add:

```bash
cd devops/docker-compose-s3 && docker compose up -d
```

- MinIO on `9000` (API) and `9001` (console), credentials `minioadmin` / `minioadmin`
- Bucket `antfly-data` created on startup by the `minio-setup` job
- Endpoint `minio:9000`, `use_ssl: false`, `addressing_style: path`

## Sharp Edges

- `storage.engine: object` outside `deployment_mode: serverless` is a config error, not a fallback
- Changing engines is an explicit backup/restore migration, not a live toggle
- The bucket allowlist and prefix boundaries are node config — rotating a credential cannot widen them
- Low-level URI flags/env overrides are supported only *without* a connection-based config; mixing the two is rejected
- Credential references are re-resolved before each backup, restore, or probe, so rotation applies without a restart — but primary object clients resolve once during serverless bootstrap, so use `default`, `profile`, or `web_identity` there
- `remote_content.s3.*` is a separate trust domain from `storage.primary` — do not share a writer credential with it
