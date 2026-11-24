# Antfly — Ops Skill

## Deployment Topologies

- **Standalone** — one process owns metadata, data, the APIs, and in-process inference. Development, demos, single-node production.
- **Lite** — one `.aflite` file opened in-process (`libantfly`, `antfly lite`), or served over HTTP with `antfly standalone --storage-engine lite`.
- **Distributed** — separate `antfly metadata` and `antfly data` processes with Raft coordination. This corpus covers the runtime processes only; Kubernetes operator deployment is out of scope.
- **Serverless** — stateless workers over object storage (`storage.engine: object`). Still **unreleased / in development** upstream (control-plane auth/quota and job tracking open); see `storage.md`.

`antfly standalone` is the canonical command. `antfly swarm` is a deprecated legacy alias for the same route; use `standalone` everywhere.

## When To Read Which Ops Module

- Local single-node setup or CLI flags:
  Read `standalone.md`
- High availability for a single server:
  Read `standalone.md` (Hot Standby)
- Auth bootstrap, backups, upgrades, install methods:
  Read `standalone.md`
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
- If the task sounds like HA for one server:
  Assume `antfly standalone` plus a hot standby (`antfly standby`)
- If the task sounds like multi-node scale-out:
  Distributed mode (`antfly metadata` + `antfly data`); Kubernetes operator deployment is out of scope for this corpus

## Standalone (Dev / Single-Node)

```bash
antfly standalone
```

Two listeners by default:
- `8080` — public API (`/db/v1`, `/ai/v1`, `/mcp/v1`). In-process inference is served here too, and `/healthz` + `/readyz` are also served at the root of this port. `/ai/v1` execution returns 403 until `public_inference.enabled` is `true`; setting `inference.api_url` removes embedded inference (and `/ai/v1`) entirely.
- `4200` — health/metrics (`/healthz`, `/readyz`, `/readyz/sql`, `/metrics`). Only `/metrics` (and `/readyz/sql`) are exclusive to this port.

Optional third: a PostgreSQL wire listener (`pgwire.enabled`, default `127.0.0.1:5432`), which requires authentication and, off loopback, `externally_protected_transport: true`.

Key flags:
- `--host` (default `127.0.0.1`), `--port` (default `8080`)
- `--health-port` (default `4200`), `--health <true|false>`
- `--config <file>` — JSON only
- `--data-dir <path>` (default `~/.antfly`)
- `--auth true` — built-in auth; first start needs `ANTFLY_BOOTSTRAP_ADMIN_PASSWORD` (12–72 bytes)
- `--secret-store-path <path>` — legacy, repeatable; prefer a config `secrets` section

Standalone defaults: `default_shards_per_table = 1`, `disable_shard_alloc = true`, auth off, public `/ai/v1` off, and no CORS middleware unless the config carries a `cors` block (which then allows no origin until `allowed_origins` lists one).

## Distributed (Production)

```bash
# Metadata node
antfly metadata --id 1 --raft-host 0.0.0.0 --raft-port 9017 \
  --api-host 0.0.0.0 --api-port 12377 \
  --cluster '{"1":{"raft_url":"http://node1:9017","orchestration_url":"http://node1:12377"}}'

# Data node
antfly data --node-id 1 --store-id 1 \
  --api-host 0.0.0.0 --api-port 12380 \
  --raft-host 0.0.0.0 --raft-port 9021 \
  --metadata-api http://node1:12377
```

Metadata node count should be odd for Raft quorum — 1, 3, or 5 are the practical choices. The `antfly metadata` runtime validates no replica parity at all, so a two-node cluster starts. Data nodes scale horizontally. Distributed nodes require `antfly.internal_service.secret`/`.issuer` — see `secrets.md`.

## Skill Modules

- [standalone.md](standalone.md) — standalone flags, defaults, auth bootstrap, hot standby, Lite, backups/upgrades, install, CLI agent mode
- [docker.md](docker.md) — Docker image, docker-compose setups
- [storage.md](storage.md) — lite / local / object engines
- [secrets.md](secrets.md) — secret store, credential management
- [inference.md](inference.md) — Antfly inference, model management
- [monitoring.md](monitoring.md) — health checks, metrics, Prometheus, Grafana
- [config.md](config.md) — configuration reference

## Critical Sharp Edges

1. Metadata replicas should be **odd** — even counts risk split-brain. The `antfly metadata` runtime enforces nothing
2. Auth-enabled instances still on legacy `admin:admin` refuse to start until `ANTFLY_BOOTSTRAP_ADMIN_PASSWORD` is set; keep published ports on `127.0.0.1` until auth and TLS (at a proxy) are in place
3. `disable_shard_alloc` defaults to `true` — automatic shard splitting is off unless you set it to `false`
4. `replication_factor` schema default is 3 (min 1, max 5) — set it to 1 explicitly for single-node dev
5. `--config` accepts **JSON only**; there is no YAML parser and no `ANTFLY_CONFIG` env var
6. Storage credentials: never hardcode — use `${secret:...}` with a secret-store file, or workload identity
7. `/metrics` lives only on the health port (4200); `/healthz` and `/readyz` are served on both 4200 and the API port (8080)
8. Process-level `storage.engine: object` requires `deployment_mode: serverless` — the config is rejected otherwise (per-table object storage on standalone/distributed is a separate feature; see `storage.md`)
9. Upgrades can migrate table files one-way — take a portable backup before upgrading; see `standalone.md`
10. Removed config keys (`admission`, `graph_execution`, flat inference keys, `keep_alive_ms`) now fail config load — see `config.md`
