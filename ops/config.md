# Configuration — Reference

## Global CLI Flags

| Flag | Env var | Default | Description |
|------|---------|---------|-------------|
| `--config` | `ANTFLY_CONFIG` | — | Config file path (JSON or YAML) |
| `--log-level` | `ANTFLY_LOG_LEVEL` | `info` | debug, info, warn, error |
| `--log-style` | `ANTFLY_LOG_STYLE` | `logfmt` | logfmt, terminal, json, noop |
| `--data-dir` | `ANTFLY_DATA_DIR` | `~/.antfly` | Root data directory |
| `--keystore-path` | `ANTFLY_KEYSTORE_PATH` | `/etc/antfly/keystore` | Encrypted keystore path |
| `--keystore-password` | `ANTFLY_KEYSTORE_PASSWORD` | — | Keystore password |

## Config File Structure

```yaml
# Cluster
metadata:
  orchestration_urls:
    "1": "http://127.0.0.1:12377"
    "2": "http://127.0.0.1:12378"
    "3": "http://127.0.0.1:12379"
replication_factor: 3
max_shards_per_table: 4

# Logging
log_level: "info"
logging_style: "json"

# CORS
cors:
  enabled: true
  allowed_origins: ["https://app.example.com"]

# S3 Storage
s3:
  enabled: true
  endpoint: "s3.amazonaws.com"
  region: "us-east-1"
  bucket: "antfly-data"
  prefix: "cluster-1"
  use_ssl: true
  access_key_id: ${secret:aws.access_key_id}
  secret_access_key: ${secret:aws.secret_access_key}

# Termite
termite:
  api_url: "http://127.0.0.1:11433"

# Storage
storage:
  local:
    base_dir: "antflydb"
  keyvalue: "local"
  metadatakv: "local"

# Limits
max_shard_size_bytes: 64000000
```

## Key Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `replication_factor` | 3 (distributed), 1 (swarm) | Number of copies per shard |
| `max_shards_per_table` | 4 | Max shards when auto-splitting |
| `max_shard_size_bytes` | 64MB | Shard size threshold for auto-split |
| `cors.enabled` | false (distributed), true (swarm) | Enable CORS headers |
| `cors.allowed_origins` | `["*"]` | Allowed CORS origins |
| `s3.enabled` | false | Use S3 storage backend |
| `termite.api_url` | — | Termite ML service URL |

## Environment Auto-Detection

- `KUBERNETES_SERVICE_HOST` set → log style defaults to `json`
- Config values support `${secret:...}` syntax → resolved via keystore/env vars

## Sharp Edges

- Config can be JSON or YAML — file extension doesn't matter, content is auto-detected
- `replication_factor` can't be changed after cluster creation — plan ahead
- `cors.allowed_origins: ["*"]` is fine for dev but should be restricted in production
- `max_shard_size_bytes` triggers auto-split — set higher for fewer, larger shards (better for S3)
- `${secret:...}` only resolves in the config file, not in API request bodies
- Swarm mode overrides several defaults — check swarm.md for the full list
