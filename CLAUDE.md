# Antfly Skills

You are working with Antfly, a distributed database and search engine with hybrid search (BM25 + vector + graph), multimodal support, and built-in RAG.

## Skills

### Backend — API, Data, Search, RAG
Read `backend/index.md` for the full overview, then load modules as needed:
- `backend/connect.md` — auth, client setup, API URL, SDKs
- `backend/schema.md` — tables, JSON Schema, x-antfly-* extensions, field types
- `backend/indexes.md` — full-text, embeddings, graph indexes and enrichments
- `backend/data.md` — insert, upsert, batch, linear merge, transforms, sync levels
- `backend/search.md` — full-text, vector, hybrid search, filters, facets, reranking
- `backend/rag.md` — retrieval agent, streaming, answer generation, citations
- `backend/integrations.md` — CDC from Postgres, S3, document sync
- `backend/auth.md` — users, API keys, RBAC, permissions
- `backend/patterns.md` — common recipes (hybrid search app, doc Q&A, image search, CDC)

### Frontend — React Components, TypeScript SDK
Read `frontend/index.md` for the overview, then:
- `frontend/sdk.md` — TypeScript SDK: client init, auth, queries, streaming, types
- `frontend/components.md` — every React component, props, wiring
- `frontend/hooks.md` — useAnswerStream, useSearchHistory, useCitations
- `frontend/patterns.md` — UI recipes: search page, Q&A chat, faceted catalog

### Ops — Deployment, Configuration, Monitoring
Read `ops/index.md` for the overview, then:
- `ops/swarm.md` — swarm mode, local dev, flags
- `ops/kubernetes.md` — K8s operator, CRDs, cloud platforms, autoscaling
- `ops/docker.md` — Docker images, docker-compose
- `ops/storage.md` — S3/R2 backend, local Pebble storage
- `ops/secrets.md` — keystore, credential management
- `ops/termite.md` — ML inference, model management
- `ops/monitoring.md` — health, metrics, Prometheus, Grafana
- `ops/config.md` — configuration reference

## Quick Reference

- API: REST at `{{ANTFLY_API_URL}}/api/v1`
- SDKs: TypeScript (`@antfly/sdk`), Go (`github.com/antflydb/antfly/pkg/client`), Python (`antfly`), Rust (`pgaf`)
- React: `@antfly/components` — QueryBox, Facet, Results, AnswerResults, RAGResults
- Auth: `Authorization: ApiKey base64(keyID:keySecret)` | Bearer | Basic | OAuth
- Deployment: `antfly swarm` (dev) | Kubernetes operator (production)
- ML: Termite (local ONNX) | Ollama | OpenAI | Gemini | Vertex | Bedrock

## Critical Sharp Edges

1. `semantic_search` requires `indexes: ["index_name"]` — omitting silently returns nothing
2. `x-antfly-types` is an array: `["text", "keyword"]` not `"text"`
3. API key header: `ApiKey base64(keyID:keySecret)` — include both ID and secret
4. Use `sync_level: "aknn"` to query vector results immediately after writing
5. Facets require `keyword` typed fields, not `text`
6. API key secret only returned once at creation — store immediately
7. `<Antfly>` provider required — all React components must be descendants
8. Import `@antfly/components/dist/components.css` — components unstyled without it
9. Metadata nodes must be odd-numbered (3 or 5) for Raft quorum
10. Termite models auto-discovered from `~/.termite/models/` — just download and go
