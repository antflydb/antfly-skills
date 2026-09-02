# Monitoring — Health, Metrics, Observability

## Health Server

The dedicated health server runs on its own port (default `4200` on `standalone`, `metadata`, and `data`; set with `--health-port`, disabled with `--health false`) and serves exactly three routes:

| Endpoint | Purpose |
|----------|---------|
| `GET /healthz` | Liveness — always returns ok while the process is up |
| `GET /readyz` | Readiness — 503 until the node is ready, then 200 |
| `GET /metrics` | Prometheus text exposition |

Which host it binds differs by runtime. `antfly standalone` hands the health server the same `--host`
as the public API, so it is loopback-only by default and remote scraping needs `--host 0.0.0.0`.
`antfly data` and `antfly metadata` always bind it to `0.0.0.0` regardless of `--api-host`.
`antfly serverless` binds it to `--host` / `ANTFLY_SERVERLESS_BIND_HOST` (default `127.0.0.1`) and has
**no default health port** at all: unless `--health-port` or `ANTFLY_SERVERLESS_HEALTH_PORT` is set,
no dedicated health server starts.

Standalone also serves `/healthz` and `/readyz` at the root of the public API port (8080); only
`/metrics` is exclusive to the health port. `--health false` shuts down the dedicated health server,
but 8080 keeps serving `/healthz` and `/readyz`.

Standalone has no `/health` route. Serverless is different: `antfly serverless` serves `/health`,
`/healthz`, `/readyz`, `/metrics`, and `/status` on its own API port.

```bash
curl http://localhost:4200/healthz
curl http://localhost:4200/readyz
```

In Kubernetes:

```yaml
livenessProbe:
  httpGet: { path: /healthz, port: 4200 }
readinessProbe:
  httpGet: { path: /readyz, port: 4200 }
  initialDelaySeconds: 10
  periodSeconds: 5
```

## Prometheus Metrics

`GET /metrics` on the health port. Prometheus text format only — there is no OpenTelemetry, StatsD, or Datadog exporter.

The exported set is large — hundreds of series across dozens of `antfly_*` families — and the
authoritative inventory is whatever `/metrics` returns on the build you are running. Scrape it and
grep rather than working from a list. Representative families:

- **Admission** — `antfly_admission_{query,write,inference}_in_flight_requests`, `_peak_in_flight_requests`, `_capacity_requests`, `_rejected_requests_total`
- **LSM** — `antfly_lsm_cache_*{kind="..."}` (kinds `run_state`, `run_table_raw`, `run_table_index`, `run_table_block`), plus `antfly_lsm_wal_*`, `antfly_lsm_compaction_*`, `antfly_lsm_owner_*`, and more
- **Resource budgets** — `antfly_resource_used_bytes{slice="..."}`, `_peak_bytes`, `_soft_limit_bytes`, `_hard_limit_bytes`, `_soft_limit_events_total`, `_hard_limit_rejections_total`, `antfly_resource_pressure` (0 normal, 1 soft, 2 hard)
- **Async indexing** — `antfly_async_index_*` counters and gauges for startup phases, WAL replay, catch-up progress, replay lag, and worker counts
- **HTTP and requests** — `antfly_http_active_connections`, `antfly_http_active_requests`, `antfly_http_body_buffer_*`, `antfly_http_*_rejections_total`, and per-request counters such as `antfly_data_api_requests_total`
- **Process and executors** — `antfly_process_*` (footprint, CPU, allocator) and `antfly_executor_*` lease/rejection counters
- **Full text, HA, inference** — `antfly_full_text_*`, `antfly_ha_*`, `antfly_inference_cache_*`, and further per-subsystem families
- **Liveness** — `antfly_data_server_up`

Cache metrics carry `kind=`, resource metrics carry `slice=`, and `antfly_lsm_owner_*` carries
per-table attribution (`table=`, `group=`, `owner_kind=`, `owner=`).

Resource slices are numerous — about thirty, spanning LSM, dense, full-text, lite, and inference
subsystems (e.g. `lsm.block_table_cache`, `lsm.compaction_work`, `dense.search_working_set`,
`full_text.segment_residency`, `text_merge.buffers`).

Interpret cache metrics together with resource-pressure metrics — the shared LSM cache is sized from the node/pod memory budget and mirrored into the `lsm.block_table_cache` hard limit.

### Prometheus Config

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "antfly"
    static_configs:
      - targets: ["antfly:4200"]
```

## Logging

Logging is configured in the config file only:

```json
{ "log": { "level": "info", "style": "json" } }
```

- `log.level`: `debug` | `info` | `warn` | `error` (default `info`)
- `log.style`: `terminal` (schema default) | `json` | `logfmt` | `noop`

There are no `--log-level` / `--log-style` CLI flags, no `ANTFLY_LOG_*` environment variables, and no automatic style switching inside Kubernetes.

## Docker Compose Observability Stack

`devops/docker-compose` bundles Prometheus (`9090`) and Grafana (`3000`) alongside Antfly. Prometheus scrapes `antfly:4200` every 15s; Grafana datasources and dashboards are provisioned from `devops/docker-compose/grafana/`.

```bash
cd devops/docker-compose && docker compose up -d
```

## Sharp Edges

- `/metrics` is on port **4200** only; `/healthz` and `/readyz` answer on both 4200 and the API port (8080)
- The health port follows `--host` under `standalone` (loopback by default, so a remote Prometheus needs `--host 0.0.0.0`); `data` and `metadata` bind it on `0.0.0.0`; `serverless` starts no health server unless you set `--health-port` or `ANTFLY_SERVERLESS_HEALTH_PORT`
- `/healthz` is liveness and always succeeds; use `/readyz` for readiness gating and load-balancer checks
- `--health false` takes down the dedicated health server, so `/metrics` disappears entirely; `/healthz` and `/readyz` remain on the API port
- `/metrics` responses are cached for ~5s, so scrape intervals below that gain nothing
- Prometheus format only — no OTel export path exists
- Set `log.style` to `json` explicitly for structured logs in Kubernetes; nothing detects the environment for you
