# Standalone — Local Development & Single-Node

## Starting Standalone

```bash
antfly standalone
```

Runs metadata, data, the public API, and in-process inference in a single process.
`antfly swarm` is a deprecated legacy alias for the same command.

### Core Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--id` | `1` | Local node id |
| `--host` | `127.0.0.1` | Public API bind host |
| `--port` | `8080` | Public API bind port |
| `--health-port` | `4200` | Dedicated health/metrics port on `--host` |
| `--health <true\|false>` | `true` | Enable the health/metrics server |
| `--config <file>` | — | Common config file, **JSON only** |
| `--data-dir <path>` | `~/.antfly` | Local Antfly data directory root |
| `--secret-store-path <path>` | — | `secrets.json` path; repeat for fallback layers |

`antfly standalone --help` lists the rest (HA hot-standby, inference memory budgets, Lite storage, ARD catalog, replica/snapshot roots).

### Ports

Standalone binds **two** ports: the API port (8080) and the health port (4200).
In-process inference is served on the API port — there is no separate inference listener.
`/healthz` and `/readyz` are served on both ports; `/metrics` is health-port only.

`12380` (data API), `9017` (metadata raft), and `9021` (data raft) are the **operator's** distributed-mode defaults, not runtime defaults. Started by hand, `antfly data` defaults `--api-port` and `--raft-port` to `0` — an OS-assigned ephemeral port — and `antfly metadata` does the same unless the port for its node id can be read out of `metadata.raft_urls` / `metadata.orchestration_urls` in a config file. Standalone binds none of them.

A separate inference server (`antfly inference run`) defaults to `127.0.0.1:8090` (`--host` / `--port`).

### Standalone Defaults

- `default_shards_per_table = 1` (schema default in other modes: 3)
- `disable_shard_alloc = true` (global default — auto-split/merge is off)
- No CORS middleware unless the config carries a `cors` block; inside one, `enabled` defaults to `true` and an omitted or empty `allowed_origins` means `["*"]`
- `replication_factor` schema default is 3 (min 1, max 5); set `1` explicitly for a single node

### Data Directory Layout

`--data-dir` (default `~/.antfly`) is the root of all durable local state:

```text
<data-dir>/
  ANTFLY_FORMAT
  secrets.json
  metadata/   replicas, catalog.txt, snapshots, auth, local-metadata.json
  data/       replicas, catalog.txt, snapshots
  inference/  ml   (traditional ML predictors)
```

Inference **model** files are not under the data directory: model discovery is deliberately
independent of the data root, so models resolve to `$ANTFLY_INFERENCE_MODELS_DIR`, else
`$HOME/.antfly/inference/models`, else `./models` when `HOME` is unset. Only the traditional-ML
directory honors `--data-dir`: `$ANTFLY_INFERENCE_ML_DIR`, else `<data-dir>/inference/ml` whenever
the runtime has a data directory, else `$HOME/.antfly/inference/ml`, else `./ml`.

Delete the directory to start fresh.

### With Config File

```bash
antfly standalone --config config.json
```

```json
{
  "replication_factor": 1,
  "default_shards_per_table": 1,
  "log": { "level": "debug", "style": "terminal" },
  "cors": {
    "enabled": true,
    "allowed_origins": ["http://localhost:3000"]
  },
  "inference": { "api_url": "http://127.0.0.1:8090" }
}
```

## Distributed Roles

```bash
antfly metadata --id 1 --raft-host 0.0.0.0 --raft-port 9017 \
  --api-host 0.0.0.0 --api-port 12377 \
  --cluster '{"1":{"raft_url":"http://node1:9017","orchestration_url":"http://node1:12377"}}'

antfly data --node-id 1 --store-id 1 \
  --api-host 0.0.0.0 --api-port 12380 \
  --raft-host 0.0.0.0 --raft-port 9021 \
  --metadata-api http://node1:12377
```

- `antfly metadata`: `--id`, `--raft-host`, `--raft-port`, `--api-host`, `--api-port`, `--cluster`
- `antfly data`: `--node-id`, `--store-id`, `--raft-host`, `--raft-port`, `--api-host`, `--api-port`, `--metadata-api` (repeatable)
- Metadata node count must be odd — any odd count works; 1, 3, or 5 are the practical choices

There is no `antfly store` command.

## Build & Run (Development)

The server is a Zig binary.

```bash
make build      # outputs ./antfly at the repo root
./antfly standalone
```

There is no `cmd/antfly` Go package and no `./bin` output directory.

## Sharp Edges

- `--config` is JSON only — a YAML file is rejected regardless of extension
- Default bind host is `127.0.0.1`; pass `--host 0.0.0.0` to accept off-host traffic
- `disable_shard_alloc` defaults to `true`, so tables do not auto-split until you set it to `false`
- Log level/style are config keys (`log.level`, `log.style`) — there are no `--log-level` / `--log-style` flags
- Inference models download on first use — the first embedding request can be slow
- CORS is off until you add a `cors` block; once present it defaults to allowing every origin, so set `allowed_origins` explicitly in production
