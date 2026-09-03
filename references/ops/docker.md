# Docker — Image & Compose

## Image

`ghcr.io/antflydb/antfly:latest` (plus version tags such as `ghcr.io/antflydb/antfly:v1.2.3`) is the single published Antfly image. There is no `:omni` tag — inference is included in the standard image.

The same image is also published to Google Artifact Registry (`us-central1-docker.pkg.dev`), with per-arch tags (`<version>-amd64`, `<version>-arm64`) alongside the multi-arch manifest; the `latest` alias is skipped for prereleases and `v0.1.x` releases.

- Multi-arch: `linux/amd64` and `linux/arm64`
- Signed with Sigstore/cosign (keyless OIDC via GitHub Actions)
- `ENTRYPOINT ["/antfly"]`, `CMD ["standalone"]`
- `EXPOSE 8080 11433 4200` (11433 is the external inference pool API port — the operator's `DefaultInferenceAPIPort`)
- Runs as UID/GID `10001`
- `HEALTHCHECK` polls `http://localhost:4200/readyz`

The Kubernetes operator ships as its own image.

## Quick Start

```bash
docker run -p 8080:8080 -p 4200:4200 \
  ghcr.io/antflydb/antfly:latest standalone --host 0.0.0.0
```

API base is `/db/v1` (inference routes are under `/ai/v1`). It is never `/api/v1`.

```bash
curl http://localhost:8080/db/v1/tables
```

## Volumes

Mount a writable path and point `--data-dir` at it. The container runs as UID 10001, so the host path must be writable by that UID.

```bash
docker run -p 8080:8080 -p 4200:4200 \
  -v "$(pwd)/antfly-data:/antflydb" \
  ghcr.io/antflydb/antfly:latest standalone --host 0.0.0.0 --data-dir /antflydb
```

Do **not** mount `/root/.antfly` — the process does not run as root.

## Custom Config

```bash
docker run -p 8080:8080 \
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

Published ports:
- `8080` — Antfly API
- `4200` — health/metrics
- `11434` — Ollama
- `9090` — Prometheus
- `3000` — Grafana

The Antfly service runs plain `standalone` with no flags. As shipped, three things do not work:

- **Neither published Antfly port is reachable.** Without `--host 0.0.0.0` the API listener binds `127.0.0.1` inside the container, and standalone gives the health server the same host — so `8080:8080` and `4200:4200` publish loopback-only listeners, and the bundled Prometheus scrape of `antfly:4200` fails for the same reason. The compose `healthcheck` still passes, because it runs *inside* the container against `localhost:4200`: the container reports healthy while nothing outside it can connect.
- **The data mount is unused.** With no `--data-dir`, standalone falls back to `$HOME/.antfly`. The published `ghcr.io/antflydb/antfly` image (built from `zig/Dockerfile.runtime`) carries no passwd entry for its numeric `USER 10001:10001` and no `/home/antfly` — that user is created only in the sibling `zig/Dockerfile` the S3 stack builds locally. So the path is not `/home/antfly/.antfly`; it is whatever `$HOME` resolves to for a passwd-less UID plus `/.antfly`, written inside the container filesystem. Either way it is not the bind mount, and `./antfly-data:/antflydb` stays empty.
- **The mounted config is never read.** `config.json` is bind-mounted at `/config.json`, but nothing passes `--config`.

Passing the flags fixes all three:

```yaml
command: ["standalone", "--host", "0.0.0.0", "--data-dir", "/antflydb", "--config", "/config.json"]
```

`--host 0.0.0.0` covers the API listener, the health/metrics listener, and therefore the Prometheus scrape. Note that the bundled `config.json` uses non-schema keys (`log_level`, `logging_style`); unknown top-level keys are ignored rather than rejected, so it loads but those two do nothing — use `log.level` and `log.style`.

## Docker Compose — S3 (MinIO)

`devops/docker-compose-s3`: MinIO plus a locally built Antfly image running `serverless combined`.

```bash
cd devops/docker-compose-s3 && docker compose up -d
```

Published ports:
- `9000` — MinIO API
- `9001` — MinIO console
- `8080` / `4200` — Antfly API and health, neither of which answers as shipped

MinIO credentials `minioadmin` / `minioadmin`; the `antfly-data` bucket is created by the `minio-setup` job. Config is mounted read-only at `/etc/antfly/config.json`. See `storage.md` for the object-storage config shape.

`antfly serverless` has **no default health port** — it takes one from `--health-port` or `ANTFLY_SERVERLESS_HEALTH_PORT`, and with neither set no dedicated health server starts. This stack sets neither, so nothing listens on 4200 and both the compose `healthcheck` and the image `HEALTHCHECK` fail permanently. Its API listener defaults to `127.0.0.1` (`ANTFLY_SERVERLESS_BIND_HOST`), so the published `8080` is loopback-only as well. Add `--host 0.0.0.0 --health-port 4200` to the command, or set `ANTFLY_SERVERLESS_BIND_HOST=0.0.0.0` and `ANTFLY_SERVERLESS_HEALTH_PORT=4200` in the environment.

## Sharp Edges

- Standalone binds `127.0.0.1` by default — pass `--host 0.0.0.0` for the published port to be reachable
- Container runs as UID 10001; bind-mounted data directories must be writable by that UID
- Readiness is `/readyz` on port 4200 (the image `HEALTHCHECK` uses it); `/healthz` is liveness only
- The S3 compose stack builds the image locally from `zig/Dockerfile` rather than pulling `ghcr.io/antflydb/antfly`
- Pin a version tag in production rather than `:latest`
- Ollama in the standard compose stack needs GPU passthrough for good throughput — CPU inference is slow for large models
