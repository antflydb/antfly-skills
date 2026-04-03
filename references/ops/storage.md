# Storage — S3, Local, Pebble

## Storage Backends

Antfly stores shard data in one of two backends:

| Backend | Best for | How it works |
|---------|----------|-------------|
| **Local (Pebble)** | Low-latency, dev | Each shard has its own Pebble instance (RocksDB successor) on local disk |
| **S3** | Cost-optimized, production | Shard data stored in S3-compatible object storage |

## S3 Backend

### Benefits
- ~87% storage cost reduction vs local NVMe
- 100-1000x faster shard splits (reference existing files, no copy)
- 30-60x faster migrations
- Only Raft leader writes to S3 — followers read shared objects (no 3x duplication)

### Configuration

```yaml
s3:
  enabled: true
  endpoint: "s3.amazonaws.com"       # or "localhost:9000" for MinIO
  region: "us-east-1"
  bucket: "antfly-production-data"
  prefix: "cluster-1/shards"
  use_ssl: true
```

### Credentials

**Preferred**: Environment variables
```bash
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

**Alternative**: Antfly keystore
```yaml
s3:
  access_key_id: ${secret:aws.access_key_id}
  secret_access_key: ${secret:aws.secret_access_key}
```

**Never** hardcode credentials in config files.

### Compatible Services

| Service | Endpoint | Notes |
|---------|----------|-------|
| AWS S3 | `s3.amazonaws.com` | Use IRSA in EKS for auth |
| Cloudflare R2 | `<account>.r2.cloudflarestorage.com` | S3-compatible, no egress fees |
| MinIO | `localhost:9000` | Local dev, `use_ssl: false` |
| Any S3-compatible | varies | Must support multipart upload |

### How It Works Internally

1. Raft leader writes SSTable files to S3
2. Followers read shared S3 objects (no duplication)
3. Shard splits reference existing S3 files (instant, no copy)
4. Background compaction gradually creates shard-specific files

## Local Storage (Pebble)

Default backend. Data stored in `--data-dir` (default: `~/.antfly`).

Each shard gets its own Pebble instance within the data directory. Raft logs stored alongside.

Delete `~/.antfly` to start completely fresh.

## Sharp Edges

- S3 adds network latency to reads — local storage is lower-latency but higher-cost
- S3 credentials rotate: if using IAM roles, ensure token refresh works
- MinIO for local dev: set `use_ssl: false` and default creds `minioadmin/minioadmin`
- S3 bucket must exist before starting Antfly — it won't create the bucket
- `prefix` in S3 config scopes all shard data under that key prefix — useful for multi-cluster on one bucket
- Switching from local to S3 requires data migration — not a live toggle
