# Monitoring — Health, Metrics, Observability

## Health Checks

| Endpoint | Port | Purpose |
|----------|------|---------|
| `GET /healthz` | 4200 (health port) | Readiness check — returns 200 when all components ready |
| `GET /health` | 4200 | Same as healthz |

Health port is separate from API port. Default: `4200`. Configurable via `--health-port`.

```bash
curl http://localhost:4200/healthz
```

In Kubernetes, use as readiness/liveness probe:
```yaml
readinessProbe:
  httpGet:
    path: /healthz
    port: 4200
  initialDelaySeconds: 10
  periodSeconds: 5
```

## Prometheus Metrics

`GET /metrics` on the health port (4200). Standard Prometheus format.

Available metrics include:
- Raft consensus (proposals, commits, leader changes)
- Storage (read/write latency, compaction, cache hits)
- Query (latency, throughput, errors by type)
- Index (embedding generation time, enrichment queue depth)
- HTTP (request count, latency by endpoint)

### Prometheus Config

```yaml
scrape_configs:
  - job_name: 'antfly'
    static_configs:
      - targets: ['localhost:4200']
    scrape_interval: 15s
```

## Logging

### Log Levels
`--log-level`: `debug`, `info` (default), `warn`, `error`

### Log Styles
`--log-style`:
- `logfmt` (default) — structured key=value pairs
- `terminal` — colorized human-readable
- `json` — structured JSON (auto-selected in Kubernetes via `KUBERNETES_SERVICE_HOST`)
- `noop` — suppress output

### Environment Variables
```bash
ANTFLY_LOG_LEVEL=debug
ANTFLY_LOG_STYLE=json
```

## Docker Compose Observability Stack

The docker-compose setup includes a pre-configured monitoring stack:

- **Prometheus** (port 9090) — scrapes `/metrics` automatically
- **Grafana** (port 3000) — visualization dashboards

```bash
cd devops/docker-compose && docker-compose up -d
```

## Sharp Edges

- Health endpoint is on port **4200**, not the API port (8080) — don't confuse them
- Metrics are Prometheus-format only — no StatsD, Datadog, or OpenTelemetry export built-in
- `json` log style is auto-selected in Kubernetes — set `--log-style terminal` explicitly if you want human-readable logs in K8s
- High-cardinality labels (per-document metrics) are avoided — metrics are per-shard/per-table granularity
