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

There are two ways to wire stores: an explicit `secrets` config section (preferred, below) or the legacy `--secret-store-path` flag. Startup rejects a config that has a `secrets` section **and** any `--secret-store-path` (or serverless `ANTFLY_SECRET_STORE_PATH`).

The legacy flag is repeatable on `standalone`, `metadata`, and `data` — most-specific first, later paths acting as read-only fallback layers; the **first** file is the writable store. `antfly serverless` takes a **single** `--secret-store-path` (a second occurrence overwrites the first) and is the only runtime that reads `ANTFLY_SECRET_STORE_PATH`.

```bash
antfly standalone \
  --config /etc/antfly/config.json \
  --secret-store-path /run/secrets/tenant/secrets.json \
  --secret-store-path /run/secrets/platform/secrets.json
```

With neither a `secrets` section nor `--secret-store-path`, standalone opens a default store at `<base>/secrets.json` **before** parsing the config, so `${secret:...}` references in the `--config` file do resolve from it. `<base>` is `--data-dir` when given, else the `storage.local.base_dir` read from the config file, else `~/.antfly`. Other runtimes have no default file store.

## Configuring Sources (`secrets`)

```json
{
  "secrets": {
    "native":  { "name": "native", "path": "/var/lib/antfly/secrets.json" },
    "sources": [
      { "name": "tenant",   "type": "file", "path": "/run/secrets/tenant/secrets.json" },
      { "name": "platform", "type": "file", "path": "/run/secrets/platform/secrets.json" }
    ],
    "environment": true
  }
}
```

- Lookup order: `native`, then `sources` in array order, then the environment (`environment` defaults to `true`; `false` disables the env fallback for references and discovery).
- `sources[].type` accepts only `file`. Names must be unique; `environment` is reserved. Paths are literal (relative to the working directory). Startup rejects a native path that overlaps a source path.
- `native` is the only API-writable store. Omit it and `PUT`/`DELETE /db/v1/secrets` are disabled. `PUT` creates a native override; `DELETE` removes only that override, so an external value can become effective again.
- `native.backend` is `file` (default; requires `path`), `distributed`, or `serverless`. The encrypted backends take `scope` (default `"default"`), `keyring_path` (required for writers), and metadata-only `grants[]` (`name`, `credential_path`, `keys`); a `distributed` data node uses `reader` (`name`, `credential_path`, `urls`) instead of `keyring_path`/`grants`. `antfly standalone` rejects any non-`file` native backend at startup.
- The section is read at startup only; file contents still rotate live.

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

`GET /db/v1/secrets` works even with no store configured — it falls back to listing the environment-variable secrets — and reports `writable` (whether a native write destination exists). Each key carries `source` (the winning source name) and `managed` (whether a native override exists). `PUT` and `DELETE` return `503 secret management requires secrets.native` when the process has no secret store or its store is not writable (for example a `secrets` section with no `native`). `DELETE` returns 404 when there is no native override, even if an external value exists.

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

1. With a `secrets` section: `native`, then each `sources[]` file in order. Otherwise: each `--secret-store-path` file in command-line order (or the standalone default `<base>/secrets.json`).
2. The environment variable named by uppercasing the key and replacing punctuation with `_` (skipped when `secrets.environment` is `false`).

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
| `antfly.internal_service.rollout_mode` | `ANTFLY_INTERNAL_SERVICE_ROLLOUT_MODE` | `migration` during a rolling upgrade from unsigned peers; `enforce` (default) otherwise |
| `antfly.trusted_principal.secret` / `.issuer` | `ANTFLY_TRUSTED_PRINCIPAL_SECRET` / `_ISSUER` | Signed proxy/gateway principals; when configured, public API requests require auth. Must differ from the internal-service secret |
| `antfly.sql_preparation.secret` / `.issuer` | — | SQL preparation authority; set both together and restart after changing. A standalone with a writable store auto-provisions it; clustered nodes need it configured. Missing → SQLSTATE `55000` |
| `antfly.setting_authority.secret` / `.issuer` | `ANTFLY_SETTING_AUTHORITY_SECRET` / `_ISSUER` | Optional distributed SQL setting/catalog-publication grants; falls back to the trusted-principal pair |

## Distributed Internal-Service Authentication

Distributed metadata and data processes require `antfly.internal_service.secret` (at least 32 random bytes) and `antfly.internal_service.issuer` provisioned identically on every node. Startup fails before opening the listener when either is missing or invalid, and the secret may not equal the trusted-principal secret.

## Kubernetes

Mount a read-only `secrets.json` (owned by the service account, mode `0600`) and list it under `secrets.sources` (or point `--secret-store-path` at it). Rotation replaces the file atomically rather than rewriting it in place.

> **Unverified:** the Kubernetes operator moved out of the Antfly repo to Colony (Antfly commit `871c143788`). The CRD fields below reflect the operator as of Antfly `ab8d9fc119` and have not been re-checked against current Colony.

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
