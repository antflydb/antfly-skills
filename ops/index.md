# Antfly — Ops Skill

## Deployment Modes

Antfly has two deployment modes:

- **Swarm mode** — single-process, runs metadata + storage + Termite together. For development and small deployments.
- **Distributed mode** — separate metadata nodes and storage nodes, each running independently. For production. Managed via the Kubernetes operator.

## Swarm Mode (Dev / Single-Node)

```bash
antfly swarm
```

Starts everything in one process. Default ports:
- `8080` — API (metadata)
- `12380` — Store API
- `9017` — Metadata Raft
- `9021` — Store Raft
- `4200` — Health/metrics
- `11433` — Termite (ML inference, enabled by default)

Key flags:
- `--termite=false` — disable ML service
- `--config <file>` — custom config (JSON or YAML)
- `--log-level debug` — verbose logging
- `--data-dir <path>` — data directory (default: `~/.antfly`)

Defaults in swarm: `replication_factor=1`, `shards_per_table=1`, CORS enabled.

## Distributed Mode (Production)

Run metadata and store nodes separately:

```bash
# Metadata node (run 3 or 5 for quorum)
antfly metadata --id 1 --raft http://0.0.0.0:9017 --api http://0.0.0.0:8080 \
  --cluster '{"1":"http://node1:9017","2":"http://node2:9017","3":"http://node3:9017"}'

# Store node (run 3+ for replication)
antfly store --id 1 --raft http://0.0.0.0:9021 --api http://0.0.0.0:12380
```

Metadata nodes must be odd-numbered (3 or 5) for Raft quorum. Store nodes scale horizontally.

## Skill Modules

- [swarm.md](swarm.md) — swarm mode config, flags, local development
- [kubernetes.md](kubernetes.md) — K8s operator, CRDs, cloud platforms, autoscaling
- [docker.md](docker.md) — Docker images, docker-compose setups
- [storage.md](storage.md) — S3/R2 backend, local storage, Pebble
- [secrets.md](secrets.md) — keystore, credential management
- [termite.md](termite.md) — ML inference service, model management
- [monitoring.md](monitoring.md) — health checks, metrics, Prometheus, Grafana
- [config.md](config.md) — configuration reference

## Critical Sharp Edges

1. Metadata nodes must be **odd-numbered** (3 or 5) — even numbers can cause split-brain
2. `antfly swarm` defaults to `replication_factor=1` — fine for dev, not production
3. Termite is enabled by default in swarm mode — disable with `--termite=false` if you don't need ML
4. S3 credentials: **never hardcode** — use env vars or keystore (`${secret:aws.access_key_id}`)
5. `wal_level = logical` for CDC requires Postgres **restart**, not just reload
6. Health endpoint: `/healthz` on the health port (4200), not the API port (8080)
7. Keystore password: set via `ANTFLY_KEYSTORE_PASSWORD` env var in production — don't pass as CLI flag
