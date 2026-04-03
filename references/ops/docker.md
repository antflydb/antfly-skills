# Docker — Images & Compose

## Images

| Image | Description |
|-------|-------------|
| `ghcr.io/antflydb/antfly:latest` | Standard image — Antfly binary only |
| `ghcr.io/antflydb/antfly:omni` | All-in-one — includes Termite ML service with ONNX Runtime |
| `ghcr.io/antflydb/antfly-operator:latest` | Kubernetes operator |

Images are multi-arch: `linux/amd64` and `linux/arm64`.

Signed with Sigstore/cosign (keyless OIDC via GitHub Actions).

## Quick Start

```bash
docker run -p 8080:8080 -p 4200:4200 ghcr.io/antflydb/antfly:latest swarm
```

This starts Antfly in swarm mode. API available at `http://localhost:8080/api/v1`.

## Docker Compose — Standard

Includes: Antfly (swarm), Ollama (embeddings), Prometheus, Grafana.

```bash
cd devops/docker-compose && docker-compose up -d
```

Ports:
- `8080` — Antfly API
- `4200` — Health/metrics
- `9090` — Prometheus
- `3000` — Grafana

## Docker Compose — S3 (MinIO)

Adds MinIO for S3-compatible storage backend.

```bash
cd devops/docker-compose-s3 && docker-compose up -d
```

Additional ports:
- `9000` — MinIO API
- `9001` — MinIO Console

MinIO default creds: `minioadmin` / `minioadmin`. Bucket auto-created on startup.

## Custom Config

Mount a config file:
```bash
docker run -v $(pwd)/config.yaml:/etc/antfly/config.yaml \
  -p 8080:8080 ghcr.io/antflydb/antfly:latest \
  swarm --config /etc/antfly/config.yaml
```

## Health Check

```bash
docker run -p 8080:8080 -p 4200:4200 \
  --health-cmd "wget -q -O- http://localhost:4200/healthz" \
  --health-interval 10s \
  ghcr.io/antflydb/antfly:latest swarm
```

## Sharp Edges

- Omni image is significantly larger due to ONNX Runtime — use standard image if you don't need local ML
- Data persists in container filesystem by default — mount a volume for durability: `-v antfly-data:/root/.antfly`
- Swarm mode in Docker uses `replication_factor=1` — single point of failure
- Ollama in docker-compose needs GPU passthrough for good performance — CPU inference is slow for large models
