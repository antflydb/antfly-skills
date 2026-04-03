---
name: antfly
description: Use this skill when working with Antfly applications, APIs, schemas, indexes, queries, retrieval-agent flows, React components, or Antfly deployment and operations. It helps choose the right Antfly feature, avoid stale component names and query shapes, and load the smallest useful backend, frontend, or ops context before coding.
---

# Antfly

Use this skill for any task that builds on, debugs, integrates with, or operates Antfly.

Start with the smallest useful context:
- Backend task:
  Read `references/backend/index.md`, then only the specific module needed
- Frontend task:
  Read `references/frontend/index.md`, then only the specific module needed
- Ops task:
  Read `references/ops/index.md`, then only the specific module needed
- Full-stack task:
  Read `references/backend/index.md` first, then `references/frontend/index.md`

Before writing code, identify:
- which table(s) are involved
- whether the task is full-text, semantic, hybrid, graph, or retrieval-agent based
- which fields must be `keyword` for filters and aggregations
- which embeddings index name is required for semantic search
- whether the environment is `antfly swarm` or distributed / Kubernetes

## Backend Routing

Read:
- `references/backend/connect.md` for auth, clients, API URL
- `references/backend/schema.md` for tables, JSON Schema, `x-antfly-*`
- `references/backend/indexes.md` for full-text, embeddings, graph indexes
- `references/backend/data.md` for inserts, batch, linear merge, sync levels
- `references/backend/search.md` for query shapes and search behavior
- `references/backend/rag.md` for retrieval agent and streaming answer flows
- `references/backend/integrations.md` for CDC and document sync
- `references/backend/auth.md` for users, API keys, RBAC
- `references/backend/patterns.md` for common recipes

Choose features this way:
- exact match / filtering / sorting:
  full-text with correct `keyword` or `numeric` fields
- semantic similarity:
  `semantic_search` with explicit `indexes`
- keyword + semantic relevance:
  hybrid search
- citation-backed answers:
  retrieval agent
- relationship traversal:
  graph indexes and graph queries

## Frontend Routing

Read:
- `references/frontend/sdk.md` for direct SDK use
- `references/frontend/components.md` for React component props and wiring
- `references/frontend/hooks.md` for custom streaming and citation handling
- `references/frontend/patterns.md` for app-level UI recipes

Choose UI this way:
- search page:
  `Antfly` + `QueryBox` + `Facet` + `ActiveFilters` + `Results`
- streaming answer UI:
  `QueryBox mode="submit"` + `AnswerResults`
- custom UI:
  `@antfly/sdk` + `useAnswerStream`

Current React surface:
- use `AnswerResults`, not `RAGResults`
- import styles from `@antfly/components/styles`

## Ops Routing

Read:
- `references/ops/swarm.md` for local single-node setup
- `references/ops/kubernetes.md` for production deployment
- `references/ops/docker.md` for Docker / compose
- `references/ops/storage.md` for storage backends
- `references/ops/secrets.md` for credentials and keystore
- `references/ops/termite.md` for model serving and inference
- `references/ops/monitoring.md` for health and metrics
- `references/ops/config.md` for exact config keys and env vars

Defaults:
- local dev / quickstart:
  assume `antfly swarm`
- production / HA / autoscaling:
  assume Kubernetes operator and distributed mode

## Critical Antfly Sharp Edges

- `semantic_search` requires `indexes: ["index_name"]`
- `x-antfly-types` is an array, not a string
- facets / aggregations require `keyword` fields
- use `sync_level: "aknn"` if vector results must be queryable immediately after writes
- API key auth is `Authorization: ApiKey base64(keyID:keySecret)`
- retrieval agent endpoint is `/api/v1/agents/retrieval`
- current React package exports `AnswerResults`, not `RAGResults`
