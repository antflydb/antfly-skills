# Secrets — Keystore & Credential Management

## Antfly Keystore

Antfly has a built-in encrypted keystore for managing secrets (API keys, cloud credentials, LLM tokens).

### Create & Manage

```bash
# Create keystore (prompts for password)
antfly keystore create

# Add secrets
antfly keystore add aws.access_key_id
antfly keystore add openai.api_key

# From stdin (scripting)
echo "sk-..." | antfly keystore add openai.api_key --stdin

# From file (e.g., GCP service account)
antfly keystore add-file gcp.credentials /path/to/service-account.json

# List secret names
antfly keystore list

# Show value
antfly keystore show openai.api_key
```

### Use in Config

Reference secrets with `${secret:key.name}` syntax:

```yaml
s3:
  access_key_id: ${secret:aws.access_key_id}
  secret_access_key: ${secret:aws.secret_access_key}

indexes:
  - type: embedding_enricher
    config:
      provider: openai
      api_key: ${secret:openai.api_key}
```

### Running with Keystore

```bash
# Via environment variable (recommended for production)
ANTFLY_KEYSTORE_PASSWORD="password" antfly swarm --config config.yaml

# Custom keystore path
antfly swarm --keystore-path /path/to/keystore
```

## Secret Resolution Order

Antfly resolves `${secret:...}` references in this order:

1. **Encrypted keystore** (if keystore exists and password provided)
2. **Environment variables** (dots → underscores, uppercased: `aws.access_key_id` → `AWS_ACCESS_KEY_ID`)
3. **Common env var mappings** (e.g., `AWS_ACCESS_KEY_ID` for `aws.access_key_id`)

## Common Secret Keys

| Key | Env var equivalent | Used for |
|-----|-------------------|----------|
| `aws.access_key_id` | `AWS_ACCESS_KEY_ID` | S3 storage |
| `aws.secret_access_key` | `AWS_SECRET_ACCESS_KEY` | S3 storage |
| `openai.api_key` | `OPENAI_API_KEY` | OpenAI embeddings/LLM |
| `anthropic.api_key` | `ANTHROPIC_API_KEY` | Anthropic LLM |
| `gemini.api_key` | `GEMINI_API_KEY` | Google Gemini |
| `gcp.credentials` | — | GCP service account JSON |
| `vertexai.project` | — | Vertex AI project ID |
| `vertexai.location` | — | Vertex AI location |

## Kubernetes

**Option 1**: Mount pre-created keystore as a K8s Secret:
```yaml
env:
  - name: ANTFLY_KEYSTORE_PASSWORD
    valueFrom:
      secretKeyRef:
        name: antfly-keystore-password
        key: password
volumeMounts:
  - name: keystore
    mountPath: /etc/antfly
    readOnly: true
volumes:
  - name: keystore
    secret:
      secretName: antfly-keystore
```

**Option 2**: Init container builds keystore from K8s Secrets at pod startup.

## Sharp Edges

- Keystore password via CLI flag is visible in `ps` output — use `ANTFLY_KEYSTORE_PASSWORD` env var instead
- Keystore is encrypted at rest — losing the password means losing access to all secrets
- `${secret:...}` syntax only works in Antfly config files, not in API requests
- Environment variables take precedence over keystore if both exist for the same key
- In Kubernetes, prefer IRSA (AWS) or Workload Identity (GCP) over keystore for cloud credentials
