# antfly-skills

Context files that make AI coding agents (Claude Code, Cursor, Codex) competent at building on [Antfly](https://antfly.io).

These aren't tutorials or documentation — they're dense, declarative context that tells an AI what Antfly can do, how concepts connect, and where the sharp edges are. The AI uses this to generate correct code for developers.

## Installation

### Claude Code

Clone this repo into your project, or add as a git submodule:

```bash
git submodule add https://github.com/antflydb/antfly-skills.git .antfly-skills
```

Claude Code will automatically read `CLAUDE.md` and discover the skill modules.

Alternatively, copy `CLAUDE.md` and the skill directories into your project root.

### Cursor

Copy `.cursorrules` into your project root:

```bash
cp antfly-skills/.cursorrules .cursorrules
```

For deeper context, also copy the `backend/`, `frontend/`, and `ops/` directories into your project.

### OpenAI Codex

Copy `AGENTS.md` into your project root:

```bash
cp antfly-skills/AGENTS.md AGENTS.md
```

For deeper context, also copy the skill directories into your project.

## What's Included

### Backend Skill

Everything an AI needs to know about Antfly's backend:

| File | Coverage |
|------|----------|
| `backend/index.md` | Overview, concept map, capabilities, SDKs, components |
| `backend/connect.md` | Auth methods, client setup, API URL |
| `backend/schema.md` | Tables, JSON Schema, x-antfly-* extensions, field types |
| `backend/indexes.md` | Full-text, embeddings, graph indexes, enrichments |
| `backend/data.md` | CRUD, batch, linear merge, transforms, sync levels |
| `backend/search.md` | Full-text, vector, hybrid search, filters, facets, reranking |
| `backend/rag.md` | Retrieval agent, streaming, answer generation, citations |
| `backend/integrations.md` | CDC from Postgres, S3, document sync |
| `backend/auth.md` | Users, API keys, RBAC, permissions |
| `backend/patterns.md` | Common recipes: hybrid search, doc Q&A, image search, CDC |

### Frontend Skill

React components and TypeScript SDK:

| File | Coverage |
|------|----------|
| `frontend/index.md` | Overview, component wiring, packages |
| `frontend/sdk.md` | TypeScript SDK: client, auth, queries, streaming, types |
| `frontend/components.md` | Every React component with props reference |
| `frontend/hooks.md` | useAnswerStream, useSearchHistory, useCitations |
| `frontend/patterns.md` | UI recipes: search page, Q&A, faceted catalog, custom input |

### Ops Skill

Deployment, configuration, and operations:

| File | Coverage |
|------|----------|
| `ops/index.md` | Overview, deployment modes, sharp edges |
| `ops/swarm.md` | Swarm mode, local dev, all flags |
| `ops/kubernetes.md` | K8s operator, CRDs, cloud platforms, autoscaling |
| `ops/docker.md` | Docker images, docker-compose setups |
| `ops/storage.md` | S3/R2 backend, local Pebble, cost comparison |
| `ops/secrets.md` | Keystore, credential management, K8s integration |
| `ops/termite.md` | ML inference, model management, quantization |
| `ops/monitoring.md` | Health checks, Prometheus metrics, logging |
| `ops/config.md` | Full configuration reference |

## Configuration

Replace `{{ANTFLY_API_URL}}` in all files with your Antfly Cloud URL (e.g., `https://acme.antfly.io`):

```bash
# macOS
find . -name "*.md" -exec sed -i '' 's|{{ANTFLY_API_URL}}|https://acme.antfly.io|g' {} +

# Linux
find . -name "*.md" -exec sed -i 's|{{ANTFLY_API_URL}}|https://acme.antfly.io|g' {} +
```

## License

Private — internal use only.
