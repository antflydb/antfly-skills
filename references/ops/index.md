# Antfly — Ops Skill

## Deployment Topologies

- **Standalone** — one process owns metadata, data, the APIs, and in-process inference. Development, demos, single-node production.
- **Distributed** — separate `antfly metadata` and `antfly data` processes with Raft coordination. Managed by the Kubernetes operator.
- **Serverless** — stateless workers over object storage (`storage.engine: object`). See `storage.md`.

`antfly standalone` is the canonical command. `antfly swarm` is a deprecated legacy alias for the same route; use `standalone` everywhere.

## When To Read Which Ops Module

- Local single-node setup or CLI flags:
  Read `standalone.md`
- Production cluster deployment:
  Read `kubernetes.md`
- Docker or compose-based setup:
  Read `docker.md`
- Object storage, local disk, or Lite:
  Read `storage.md`
- Secrets / credentials:
  Read `secrets.md`
- Model serving and inference:
  Read `inference.md`
- Health, metrics, logs:
  Read `monitoring.md`
- Exact config keys and env vars:
  Read `config.md`

## Environment Defaults

- If the task sounds like local development, demos, or quickstart:
  Assume `antfly standalone`
- If the task sounds like HA, autoscaling, or production:
  Assume Kubernetes operator and distributed mode

## Standalone (Dev / Single-Node)

```bash
antfly standalone
```

Two listeners:
- `8080` — public API (`/db/v1`, `/ai/v1`). In-process inference is served here too, and `/healthz` + `/readyz` are also served at the root of this port.
- `4200` — health/metrics (`/healthz`, `/readyz`, `/metrics`). Only `/metrics` is exclusive to this port.

Key flags:
- `--host` (default `127.0.0.1`), `--port` (default `8080`)
- `--health-port` (default `4200`), `--health <true|false>`
- `--config <file>` — JSON only
- `--data-dir <path>` (default `~/.antfly`)
- `--secret-store-path <path>` — repeatable

Standalone defaults: `default_shards_per_table = 1`, `disable_shard_alloc = true`, and no CORS middleware unless the config carries a `cors` block.

## Distributed (Production)

```bash
# Metadata node (the odd-replica rule is an operator webhook check, not a runtime one)
antfly metadata --id 1 --raft-host 0.0.0.0 --raft-port 9017 \
  --api-host 0.0.0.0 --api-port 12377 \
  --cluster '{"1":{"raft_url":"http://node1:9017","orchestration_url":"http://node1:12377"}}'

# Data node
antfly data --node-id 1 --store-id 1 \
  --api-host 0.0.0.0 --api-port 12380 \
  --raft-host 0.0.0.0 --raft-port 9021 \
  --metadata-api http://node1:12377
```

Metadata node count should be odd for Raft quorum — 1, 3, or 5 are the practical choices. The odd-count rule is enforced only by the operator's admission webhook on `spec.metadataNodes.replicas`; the raw `antfly metadata` runtime validates no replica parity at all, so a hand-rolled two-node cluster starts. Data nodes scale horizontally.

## Skill Modules

- [standalone.md](standalone.md) — standalone flags, defaults, local development
- [kubernetes.md](kubernetes.md) — K8s operator, CRDs, cloud platforms, autoscaling
- [docker.md](docker.md) — Docker image, docker-compose setups
- [storage.md](storage.md) — lite / local / object engines
- [secrets.md](secrets.md) — secret store, credential management
- [inference.md](inference.md) — Antfly inference, model management
- [monitoring.md](monitoring.md) — health checks, metrics, Prometheus, Grafana
- [config.md](config.md) — configuration reference

## Critical Sharp Edges

1. Metadata replicas should be **odd** — even counts risk split-brain. The operator's admission webhook rejects even counts (any odd number passes; 1, 3, and 5 are the recommended sizes); the raw `antfly metadata` runtime enforces nothing
2. **`spec.metadataNodes.replicas` is immutable after creation** — the operator webhook rejects any change, 3 → 5 included. Resizing means standing up a differently named cluster at the target count on fresh metadata PVCs and restoring a backup into it
3. `disable_shard_alloc` defaults to `true` — automatic shard splitting is off unless you set it to `false`
4. `replication_factor` schema default is 3 (min 1, max 5) — set it to 1 explicitly for single-node dev
5. `--config` accepts **JSON only**; there is no YAML parser and no `ANTFLY_CONFIG` env var
6. Storage credentials: never hardcode — use `${secret:...}` with a secret-store file, or workload identity
7. `/metrics` lives only on the health port (4200); `/healthz` and `/readyz` are served on both 4200 and the API port (8080)
8. Object storage requires `deployment_mode: serverless` — the config is rejected otherwise
