# Secrets — Secret Store & Credential Management

## The Secret Store

Antfly resolves secret references from a plaintext JSON file protected by operating-system file permissions. It is deliberately **not** an encrypted keystore: disk encryption or a platform secret volume must provide encryption at rest.

```json
{
  "secrets": [
    { "key": "openai.api_key", "value": "REDACTED" },
    { "key": "storage.access_key_id", "value": "REDACTED" }
  ]
}
```

Pass it with `--secret-store-path`. The flag is repeatable on `standalone`, `metadata`, and `data` — most-specific first, later paths acting as fallback layers. `antfly serverless` takes a **single** `--secret-store-path` (a second occurrence overwrites the first) and is the only runtime that reads `ANTFLY_SECRET_STORE_PATH`. The operator injects that env var on the standalone, metadata, and data StatefulSets too, where it does nothing; those pods work because the operator also passes `--secret-store-path` on their command lines.

```bash
antfly standalone \
  --config /etc/antfly/config.json \
  --secret-store-path /run/secrets/tenant/secrets.json \
  --secret-store-path /run/secrets/platform/secrets.json
```

Standalone opens a default store at `<data-dir>/secrets.json`, but it opens it *after* the config file is parsed. As shipped, `${secret:...}` references inside a `--config` file are therefore never resolved from that default store: with no explicit `--secret-store-path`, config-time resolution has no store at all and falls straight through to the environment-variable fallback, failing startup with `SecretNotFound` when the variable is absent — even if `<data-dir>/secrets.json` holds the key. The default store serves only the `/db/v1/secrets` API and the internal-service-auth lookups. Pass `--secret-store-path` explicitly whenever the config references secrets; pointing it at `<data-dir>/secrets.json` is fine.

Updates are picked up on reload. A malformed or missing replacement keeps the last-known-good in-memory snapshot and reports stale state; startup fails closed when a required reference cannot be resolved.

## Managing Secrets Through the API

The authenticated management API can list, put, and delete keys. **Values are never returned.**

```bash
curl -X PUT https://antfly.example.com/db/v1/secrets/openai.api_key \
  -H 'Authorization: Bearer TOKEN' -H 'Content-Type: application/json' \
  --data '{"value":"REDACTED"}'

curl https://antfly.example.com/db/v1/secrets -H 'Authorization: Bearer TOKEN'

curl -X DELETE https://antfly.example.com/db/v1/secrets/openai.api_key \
  -H 'Authorization: Bearer TOKEN'
```

`GET /db/v1/secrets` works even with no store configured — it falls back to listing the environment-variable secrets. `PUT` and `DELETE` return `503 secret management not available in multi-node mode` only when the process has no secret store at all, as on a data node. Writability is never probed: a read-only store file accepts the request and then fails with an I/O error when the write is persisted, not with a 503.

## Use in Config

```json
{
  "connections": {
    "openai-production": {
      "kind": "inference",
      "capabilities": ["models.generate", "models.embed"],
      "inference": {
        "provider": "openai",
        "api_key": "${secret:openai.api_key}"
      }
    }
  }
}
```

References have the exact form `${secret:key.name}`. Keys may contain ASCII letters, numbers, `.`, `_`, and `-`.

References also resolve in foreign-source and CDC DSNs sent in API request bodies, so they are not limited to the config file.

## Resolution Order

1. Each `--secret-store-path` file, in command-line order.
2. The environment variable named by uppercasing the key and replacing punctuation with `_`.

`openai.api_key` → `OPENAI_API_KEY`.

## Common Secret Keys

| Key | Env var equivalent | Used for |
|-----|-------------------|----------|
| `openai.api_key` | `OPENAI_API_KEY` | OpenAI embeddings/generation |
| `anthropic.api_key` | `ANTHROPIC_API_KEY` | Anthropic generation |
| `gemini.api_key` | `GEMINI_API_KEY` | Google Gemini |
| `cohere.api_key` | `COHERE_API_KEY` | Cohere |
| `storage.access_key_id` | `STORAGE_ACCESS_KEY_ID` | Static S3-compatible storage credentials |
| `storage.secret_access_key` | `STORAGE_SECRET_ACCESS_KEY` | Static S3-compatible storage credentials |
| `antfly.internal_service.secret` | `ANTFLY_INTERNAL_SERVICE_SECRET` | Distributed node-to-node `/internal/v1` RPC |
| `antfly.internal_service.issuer` | `ANTFLY_INTERNAL_SERVICE_ISSUER` | Distributed internal-auth issuer |

## Distributed Internal-Service Authentication

Distributed metadata and data processes require `antfly.internal_service.secret` (at least 32 random bytes) and `antfly.internal_service.issuer` provisioned identically on every node. Startup fails before opening the listener when either is missing or invalid, and the secret may not equal the trusted-principal secret.

## Kubernetes

Mount a read-only `secrets.json` (owned by the service account, mode `0600`) and point `--secret-store-path` at it. Rotation replaces the file atomically rather than rewriting it in place.

The operator references Secrets by name only — it never reads their values:

```yaml
apiVersion: antfly.io/v1
kind: AntflyCluster
spec:
  secretStore:
    secretName: antfly-secret-store   # required; a Secret in this namespace
    key: secrets.json                 # optional, defaults to secrets.json
    path: /run/antfly/secrets/secrets.json   # optional, this is the default
  internalServiceAuth:
    secretKeyRef:
      name: antflydb-internal-service-auth
      key: secret
      optional: false
```

Treat each internal-service Secret as immutable; rotate with versioned Secrets via `nextSecretKeyRef` and wait for `status.internalServiceAuthRotation.phase: Switched` before promoting.

## Sharp Edges

- The store file is **plaintext JSON** — protect it with filesystem permissions and a platform secret volume; never commit it or bake it into an image
- Never pass secrets as process arguments — they appear in process listings
- Environment variables are a fallback, not an override: store files are checked first, in CLI order
- The `/db/v1/secrets` API never returns values, only key metadata
- Prefer IRSA (AWS) or Workload Identity (GCP) over static keys for cloud credentials
- Primary storage credentials (`connections.*` with `storage.primary`) and remote-content credentials (`remote_content.s3.*`) are separate trust domains — do not reuse one for the other
