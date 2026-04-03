# Swarm Mode — Local Development & Single-Node

## Starting Swarm

```bash
antfly swarm
```

Runs metadata server, storage node, and Termite ML service in a single process.

### All Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--id` | 1 | Node ID |
| `--metadata-raft` | `http://0.0.0.0:9017` | Metadata Raft URL |
| `--metadata-api` | `http://0.0.0.0:8080` | Metadata API URL |
| `--metadata-cluster` | `{"1":"http://0.0.0.0:9017"}` | Cluster peer URLs (JSON) |
| `--store-raft` | `http://0.0.0.0:9021` | Store Raft URL |
| `--store-api` | `http://0.0.0.0:12380` | Store API URL |
| `--termite` | `true` | Enable Termite ML service |
| `--termite-api-url` | `http://0.0.0.0:11433` | Termite API URL |
| `--health-port` | `4200` | Health/metrics port |
| `--config` | — | Config file path (JSON or YAML) |
| `--log-level` | `info` | Log level: debug, info, warn, error |
| `--log-style` | `logfmt` | Output: logfmt, terminal, json, noop |
| `--data-dir` | `~/.antfly` | Root data directory |

### Swarm Defaults

These are set automatically in swarm mode (differ from distributed):
- `replication_factor = 1` (distributed default: 3)
- `default_shards_per_table = 1`
- `CORS = enabled`
- `DisableShardAlloc = true`

### With Config File

```bash
antfly swarm --config config.yaml
```

```yaml
log_level: debug
cors:
  enabled: true
  allowed_origins: ["http://localhost:3000"]
termite:
  api_url: "http://127.0.0.1:11433"
max_shard_size_bytes: 64000000
```

## Go Run (Development)

```bash
go run ./cmd/antfly swarm
```

With SIMD acceleration (recommended):
```bash
GOEXPERIMENT=simd go run ./cmd/antfly swarm
```

Or via Makefile:
```bash
make build && ./bin/antfly swarm
```

## Sharp Edges

- Swarm mode uses `replication_factor=1` — data is not replicated. Fine for dev, not production.
- Termite downloads models on first use — first embedding request may be slow
- `--data-dir` stores all Raft logs, Pebble data, and indexes — delete to start fresh
- Port conflicts: if 8080 is taken, the API won't start. Check all 6 ports are available.
- CORS is enabled by default — in production, configure `allowed_origins` explicitly
