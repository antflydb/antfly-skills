# Docker — Image & Compose

## Image

`ghcr.io/antflydb/antfly:latest` (plus immutable semantic-version tags) is the single published Antfly image. There is no `:omni` tag — inference is included in the standard image.

The same image is also published to Google Artifact Registry. Semantic-version tags are immutable; channel tags move: `latest` (stable), `next` (prereleases), `nightly`, and per-line `v0-3` / `v0-3-next`.

- Multi-arch: `linux/amd64` and `linux/arm64`
- Signed with Sigstore/cosign (keyless OIDC via GitHub Actions)
- `ENTRYPOINT ["/antfly"]`, `CMD ["standalone"]`
- Base `debian:bookworm-slim`; the binary is the glibc (`_gnu`) build with CUDA runtime libraries (cuBLASLt, cuDNN, cudart, NVRTC) bundled — GPUs still need the host driver
- `EXPOSE 8080 11433 4200`. Nothing in the Antfly runtime binds 11433 by default; it was the operator's external inference-pool port convention, and the operator now lives in Colony
- Runs as user `antfly` (UID/GID `10001`, home `/home/antfly`); `/antflydb` is pre-created and owned by `10001:10001`
- `HEALTHCHECK` polls `http://localhost:4200/readyz`

The Kubernetes operator is no longer built from the Antfly repo (moved to Colony).

## Quick Start

```bash
docker run -p 127.0.0.1:8080:8080 -p 127.0.0.1:4200:4200 \
  --ulimit nofile=65536:65536 \
  ghcr.io/antflydb/antfly:latest standalone --host 0.0.0.0
```

`--host 0.0.0.0` is needed inside the container; publish on host `127.0.0.1` until auth and TLS are configured. Without `--data-dir`, state lands in `/home/antfly/.antfly` inside the container filesystem.

API base is `/db/v1` (inference routes are under `/ai/v1`). It is never `/api/v1`.

```bash
curl http://localhost:8080/db/v1/tables
```

## Volumes

Mount a writable path and point `--data-dir` at it. The container runs as UID 10001, so the host path must be writable by that UID.

```bash
docker run -p 127.0.0.1:8080:8080 -p 127.0.0.1:4200:4200 \
  -v antfly-data:/antflydb \
  ghcr.io/antflydb/antfly:latest standalone --host 0.0.0.0 --data-dir /antflydb
```

A named volume inherits the image's `10001`-owned `/antflydb`; a host bind mount must be writable by UID 10001. Do **not** mount `/root/.antfly` — the process does not run as root.

## Auth in Docker

Forward the bootstrap password by name so its value never appears in the command line:

```bash
export ANTFLY_BOOTSTRAP_ADMIN_PASSWORD="$(openssl rand -base64 24)"
docker run -p 127.0.0.1:8080:8080 --env ANTFLY_BOOTSTRAP_ADMIN_PASSWORD \
  -v antfly-data:/antflydb ghcr.io/antflydb/antfly:latest \
  standalone --host 0.0.0.0 --data-dir /antflydb --auth true
```

Pull models into a running container with `docker exec <container> antfly inference pull <owner/model>`.

## Custom Config

```bash
docker run -p 127.0.0.1:8080:8080 \
  -v "$(pwd)/config.json:/etc/antfly/config.json:ro" \
  ghcr.io/antflydb/antfly:latest \
  standalone --host 0.0.0.0 --config /etc/antfly/config.json
```

Config is JSON only.

## Docker Compose — Standard

`devops/docker-compose`: Antfly (`standalone`) + Ollama + Prometheus + Grafana.

```bash
cd devops/docker-compose && docker compose up -d
```

The Antfly service runs:

```yaml
command: ["standalone", "--host", "0.0.0.0", "--data-dir", "/antflydb", "--config", "/config.json"]
```

with `./antfly-data:/antflydb` and `./config.json:/config.json:ro` mounted. The bundled `config.json` sets only `log.level: info` and `log.style: json`.

Published ports, all bound to host `127.0.0.1`:
- `8080` — Antfly API
- `4200` — health/metrics
- `11434` — Ollama
- `9090` — Prometheus
- `3000` — Grafana

Remaining caveats:

- The compose file sets `ANTFLY_LOG_LEVEL=info`, which Antfly never reads; logging comes only from `log.*` in `config.json`.
- The compose `healthcheck` polls `/healthz` (liveness), not `/readyz` — a container can report healthy before it is ready. The image's own `HEALTHCHECK` uses `/readyz`.
- Prometheus mounts the shared `devops/prometheus.yml` (scrapes `antfly:4200` every 15s).
- Auth is off. Keep the `127.0.0.1` bindings until auth and TLS termination are configured.

## Docker Compose — S3 (MinIO)

`devops/docker-compose-s3`: MinIO plus a locally built Antfly image running `serverless combined`.

```bash
cd devops/docker-compose-s3 && docker compose up -d
```

The Antfly service runs `serverless combined --config /etc/antfly/config.json --host 0.0.0.0 --health-port 4200`; its compose `healthcheck` polls `/readyz` on 4200.

Published ports, all bound to host `127.0.0.1`:
- `9000` — MinIO API
- `9001` — MinIO console
- `8080` / `4200` — Antfly API and health

MinIO root credentials `minioadmin` / `minioadmin`; the `antfly-data` bucket is created by the `minio-setup` job. Antfly reaches MinIO with the same pair through `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION=us-east-1` in its environment (the `credentials` block is omitted, so the default AWS chain applies). Config is mounted read-only at `/etc/antfly/config.json`; a named volume backs `/tmp/antfly-serverless-cache`. See `storage.md` for the object-storage config shape. Serverless itself is still unreleased upstream.

`antfly serverless` has **no default health port** — without `--health-port` or `ANTFLY_SERVERLESS_HEALTH_PORT` no dedicated health server starts — and its API listener defaults to `127.0.0.1` (`ANTFLY_SERVERLESS_BIND_HOST`). The shipped stack passes both flags; keep them if you adapt it.

## Sharp Edges

- Standalone binds `127.0.0.1` by default — pass `--host 0.0.0.0` inside the container, and publish on host `127.0.0.1` until auth/TLS are set up
- Container runs as UID 10001; bind-mounted data directories must be writable by that UID
- Standalone refuses to start with `RLIMIT_NOFILE` < 256 and warns below 65536 — pass `--ulimit nofile=65536:65536`
- Never put `ANTFLY_BOOTSTRAP_ADMIN_PASSWORD=<value>` on the command line; forward it with `--env ANTFLY_BOOTSTRAP_ADMIN_PASSWORD`
- Readiness is `/readyz` on port 4200 (the image `HEALTHCHECK` uses it); `/healthz` is liveness only
- The S3 compose stack builds the image locally from `zig/Dockerfile` rather than pulling `ghcr.io/antflydb/antfly`
- Pin a version tag in production rather than `:latest`
- Ollama in the standard compose stack needs GPU passthrough for good throughput — CPU inference is slow for large models
