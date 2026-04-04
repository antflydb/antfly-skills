# Plan: antfly-skills v2 — Agent Operability

## Context

antfly-skills v1 teaches an AI agent **what Antfly is**. Codex's comparison against Supabase/Neon revealed the gap: we don't teach agents **how to safely connect, inspect, scaffold, verify, debug, and evolve** an Antfly deployment. This plan closes that gap.

**What exists today** (already shipped in antfly-skills repo):
- 3 skills (backend, frontend, ops) with concept docs and sharp edges
- MCP + A2A protocol documentation (tools, setup snippets)
- SKILL.md, CLAUDE.md, .cursorrules, AGENTS.md entrypoints

**What's missing** (Codex's priority list, filtered to what we can build now):

| # | Item | New file |
|---|------|----------|
| 1 | MCP/A2A client setup recipes (every IDE, copy-paste) | `references/backend/mcp-setup.md` |
| 2 | Capability matrix (exact tool/action catalog) | `references/backend/capabilities.md` |
| 3 | Safe operating modes + prod guardrails | `references/backend/safety.md` |
| 4 | Golden path (setup → first semantic query → first RAG) | `references/getting-started.md` |
| 5 | Environment contract (.env template, all vars) | `references/ops/environment.md` |
| 6 | Troubleshooting runbooks | `references/troubleshooting.md` |
| 10 | Prompt cookbook ("when user asks X, do Y") | `references/cookbook.md` |

Items 7 (change management), 8 (introspection/codegen), 9 (starter templates) are deferred — they need product features or AJ input.

---

## New Files

### `references/backend/mcp-setup.md` — Copy-Paste MCP/A2A Config for Every IDE

Expand the current mcp.md setup section into a complete recipe file with:

- **Claude Code**: full JSON config for `.claude/settings.json` (both project and user level)
- **Cursor**: `.cursor/mcp.json` config
- **Codex / other**: generic MCP client config
- **Local dev**: `http://localhost:8080/mcp/v1/` with `antfly swarm`
- **Cloud**: `https://<org>.antfly.io/mcp/v1/`
- **A2A setup**: how to point an A2A-compatible agent at `/.well-known/agent.json`
- **Verify connection**: step-by-step — call `list_tables`, expect empty array, success

~200 lines.

### `references/backend/capabilities.md` — Exact Capability Matrix

A single dense table an agent can scan to know exactly what's possible:

**MCP Tools** (10):
| Tool | Action | Mutates? | Args summary |
|------|--------|----------|-------------|
| `list_tables` | Enumerate tables | No | — |
| `create_table` | Create table + default full-text index | Yes | tableName, numShards, fields |
| `drop_table` | Remove table | Yes (destructive) | tableName |
| `list_indexes` | List indexes + shard status | No | tableName |
| `create_index` | Add index (validates embedder) | Yes | tableName, indexName, field/template, embedder JSON |
| `drop_index` | Remove index | Yes (destructive) | tableName, indexName |
| `query` | Search (full-text, semantic, hybrid) | No | tableName, fullTextSearch, semanticSearch, indexes, limit |
| `batch` | Insert/delete documents | Yes | tableName, writes, deletes |
| `backup` | Create table backup | No (creates snapshot) | tableName, backupID, location |
| `restore` | Restore from backup | Yes | tableName, backupID, location |

**A2A Skills** (2):
| Skill | Action | Streaming? |
|-------|--------|-----------|
| `retrieval` | RAG: multi-strategy search + LLM answer | Yes |
| `query-builder` | Natural language → Bleve query JSON | No |

**REST API** (not available via MCP):
| Action | Endpoint | Why not in MCP |
|--------|----------|---------------|
| Linear merge (bulk import) | `POST /{table}/linear-merge` | Complex cursor workflow |
| Transforms ($set, $inc, etc.) | `POST /{table}/batch` | MCP batch only does insert/delete |
| Lookup by key | `GET /{table}/keys/{key}` | Use REST directly |
| Transaction | `POST /transaction` | Multi-table atomic |
| User management | `/users/*` | Auth/admin scope |
| Facets/aggregations | via `/query` | Available in MCP query, but aggregation config must go through REST |

~150 lines.

### `references/backend/safety.md` — Safe Operating Modes & Guardrails

Critical file. Based on actual code analysis:

**Current state**: MCP server has **no auth, no read-only mode, no permission checks**. All 10 tools are fully mutable and unrestricted. This is important for agents to know.

Content:
- **MCP has no auth today** — any client that can reach the endpoint can create/drop tables. In local dev this is fine. In production, restrict network access.
- **Dangerous actions list**: `drop_table`, `drop_index`, `batch` with deletes, `restore` (overwrites data). Agent should confirm with user before executing these.
- **Safe actions**: `list_tables`, `list_indexes`, `query`, `backup` — read-only or non-destructive.
- **Local dev default**: Assume `antfly swarm` on localhost unless told otherwise. Don't point at production without explicit user confirmation.
- **Prod guardrails**: Don't create/drop tables in production via MCP. Use REST API with proper auth. MCP is best for dev/staging.
- **Approval-required operations**:
  - Dropping tables or indexes
  - Batch deletes
  - Restoring from backup
  - Creating indexes (blocks for up to 30s while validating embedder)
- **Timeouts to know about**: Embedder validation = 30s timeout. Transport = 10s. Health check = instant.

~200 lines.

### `references/getting-started.md` — Golden Path (Setup to First Success)

A deterministic bootstrap workflow an agent can follow:

**Step 1: Start Antfly**
```bash
antfly swarm
```
Verify: `curl http://localhost:4200/healthz` → "ok"

**Step 2: Configure MCP** (copy-paste config for IDE of choice — link to mcp-setup.md)

**Step 3: Verify connection**
MCP: `list_tables` → expect empty array

**Step 4: Create a table**
MCP: `create_table` with tableName="demo", fields: `{ "title": "string", "content": "string", "category": "string" }`

**Step 5: Create an embeddings index**
MCP: `create_index` with embedder config (ollama + nomic-embed-text for local, or openai for cloud)
Note: blocks up to 30s while validating embedder. If Termite is running, use termite provider.

**Step 6: Insert a document**
MCP: `batch` with writes: `{ "doc-1": { "title": "Hello", "content": "This is a test document", "category": "test" } }`

**Step 7: Run a full-text search**
MCP: `query` with fullTextSearch: `"title:Hello"`, tableName: "demo"

**Step 8: Run a semantic search**
MCP: `query` with semanticSearch: "greeting", indexes: ["your_index_name"], tableName: "demo"
Important: must specify `indexes` or get zero results.

**Step 9: Run a retrieval agent request** (via A2A or REST)
`POST /api/v1/agents/retrieval` with query + table + generator config

**Step 10: Validate health**
`curl http://localhost:4200/readyz` → "ready"
`curl http://localhost:4200/metrics` → Prometheus metrics

~250 lines.

### `references/ops/environment.md` — Environment Contract

Canonical .env template and all variables:

```env
# Required
ANTFLY_API_URL=http://localhost:8080          # API base URL

# Auth
# API key format: Authorization: ApiKey base64(keyID:keySecret)

# Antfly Server Config
ANTFLY_CONFIG=                                # Config file path (JSON or YAML)
ANTFLY_LOG_LEVEL=info                         # debug, info, warn, error
ANTFLY_LOG_STYLE=logfmt                       # logfmt, terminal, json, noop
ANTFLY_DATA_DIR=~/.antfly                     # Root storage directory
ANTFLY_HEALTH_PORT=4200                       # Health/metrics port

# Keystore
ANTFLY_KEYSTORE_PATH=~/.antfly/.secrets
ANTFLY_KEYSTORE_PASSWORD=                     # Prefer env var over CLI flag

# Swarm Mode
ANTFLY_SWARM_METADATA_API=http://0.0.0.0:8080
ANTFLY_SWARM_STORE_API=http://0.0.0.0:12380
ANTFLY_SWARM_TERMITE=true

# Termite (ML)
ANTFLY_TERMITE_API_URL=                       # Empty = no Termite proxy

# Model Providers
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
COHERE_API_KEY=

# S3 Storage
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# Content Security
ANTFLY_CONTENT_SECURITY_BLOCK_PRIVATE_IPS=true
ANTFLY_CONTENT_SECURITY_MAX_DOWNLOAD_SIZE_BYTES=104857600
```

Plus: swarm vs distributed mode assumptions, where Termite lives, where logs/metrics are, K8s auto-detection.

~150 lines.

### `references/troubleshooting.md` — Debugging Runbooks

Structured as: **Symptom → Cause → Fix**

**Semantic search returns zero results**
- Missing `indexes` parameter (most common) — add `indexes: ["your_index_name"]`
- Embeddings not ready yet — use `sync_level: "aknn"` on writes, or wait for enrichment
- Wrong index name — check with `list_indexes`
- Empty table — verify data was inserted

**Embeddings not generating / index creation hangs**
- Termite not running — check `curl http://localhost:11433/health`
- Model not downloaded — run `antfly termite pull --variants i8 BAAI/bge-small-en-v1.5`
- 30-second timeout on embedder validation — embedder config invalid or provider unreachable
- Dimension mismatch — auto-detection failed, specify dimension explicitly

**Retrieval agent / streaming fails**
- Generator not configured — provide `generator: { provider, model }` in request
- SSE client required — REST endpoint streams `text/event-stream`, not JSON
- A2A endpoint is `/a2a` (JSON-RPC), REST endpoint is `/api/v1/agents/retrieval` (SSE) — don't mix them

**Auth failures**
- API key format wrong — must be `ApiKey base64(keyID:keySecret)`, not just the secret
- Key expired or deleted — create new key, secret only shown once
- New user has zero permissions — explicitly grant permissions after creation
- MCP has no auth — if MCP works but REST doesn't, it's an auth header issue

**Termite / model issues**
- "model not found" — run `antfly termite list` to see available models
- Slow first request — model loads on demand, first inference is slow
- CPU inference slow for large models — use `i8` quantized variants
- `--termite=false` disables ML entirely — no embeddings, chunking, or reranking

**Cluster / storage issues**
- Split-brain — metadata nodes must be odd (3 or 5)
- Shard not found — table may not have finished creating, check with `list_tables`
- S3 bucket doesn't exist — Antfly doesn't create it, must exist before startup
- Health endpoint on port 4200, not 8080 — don't confuse them

~300 lines.

### `references/cookbook.md` — Prompt Cookbook

"When the user asks X, do Y" — concrete agent recipes.

**"Add semantic search to my app"**
1. Read `references/backend/indexes.md` for embeddings config
2. Check if table exists (MCP: `list_tables`)
3. Create embeddings index with appropriate template + provider
4. If data already exists, it needs re-indexing (enrichments run on new writes, not retroactively)
5. Update queries to include `semantic_search` + `indexes` parameter
6. For UI: add `semanticIndexes` prop to `<Results>` or use `<AnswerResults>`

**"Set up local Antfly"**
1. `antfly swarm` (or `docker run ... antfly swarm`)
2. Verify: `curl localhost:4200/healthz`
3. Configure MCP in IDE (link to mcp-setup.md)
4. Follow golden path (link to getting-started.md)

**"Debug empty search results"**
1. Check `indexes` parameter present for semantic search
2. MCP: `list_indexes` — verify index exists and is healthy
3. MCP: `list_tables` — verify table has data
4. Try full-text search first (simpler) to isolate vector vs query issues
5. Check sync_level — data may not be indexed yet

**"Create MCP config"**
1. Determine environment (local swarm vs cloud)
2. Generate IDE-specific config (link to mcp-setup.md)
3. Test with `list_tables`

**"Wire retrieval agent / A2A flow"**
1. Read `references/backend/a2a.md`
2. Ensure table has embeddings index
3. Choose mode: pipeline (simple) or agentic (multi-turn)
4. Configure generator (provider + model)
5. Handle streaming events in order: classification → reasoning → hits → answer → followups → done

**"Add Antfly React components to my app"**
1. `npm install @antfly/components @antfly/sdk`
2. Import CSS: `import '@antfly/components/styles'`
3. Wrap app in `<Antfly url={...} table={...}>`
4. For search: `<QueryBox>` + `<Results>` with `semanticIndexes`
5. For Q&A: `<QueryBox mode="submit">` + `<AnswerResults>` with generator config
6. Read `references/frontend/components.md` for full props reference

**"Switch embedding model"**
1. Cannot change model on existing index — embeddings are model-specific
2. Create new index with new model config
3. Data will be re-enriched with new embeddings on next write
4. For existing data: need to trigger re-indexing (touch or re-insert documents)
5. Once new index is ready, update queries to use new index name
6. Drop old index

~300 lines.

---

## Updated File Structure

```
references/
├── getting-started.md          # NEW: golden path setup → first success
├── troubleshooting.md          # NEW: symptom → cause → fix runbooks
├── cookbook.md                  # NEW: "when user asks X, do Y"
├── backend/
│   ├── (existing files...)
│   ├── mcp-setup.md            # NEW: copy-paste MCP/A2A config for every IDE
│   ├── capabilities.md         # NEW: exact tool/action matrix
│   └── safety.md               # NEW: safe operating modes, guardrails
├── frontend/
│   └── (existing files...)
└── ops/
    ├── (existing files...)
    └── environment.md           # NEW: canonical .env template, all vars
```

7 new files. Estimated ~1,550 lines total.

---

## Entrypoint Updates

### SKILL.md
Add to the top, after "Agent Protocols":
- Link to `references/getting-started.md` as "first-time setup"
- Link to `references/backend/safety.md` as "before operating"
- Link to `references/troubleshooting.md` as "when something goes wrong"
- Link to `references/cookbook.md` as "common agent tasks"

### .cursorrules
Add a "## Safety" section with the dangerous actions list and local-dev-default rule.
Add a "## Troubleshooting" one-liner pointing to the full runbook.

### CLAUDE.md / AGENTS.md
Add links to getting-started.md, safety.md, troubleshooting.md, cookbook.md.

---

## Build Sequence

1. `references/backend/capabilities.md` — smallest, most mechanical
2. `references/backend/mcp-setup.md` — copy-paste configs
3. `references/backend/safety.md` — guardrails and dangerous actions
4. `references/ops/environment.md` — .env template
5. `references/getting-started.md` — golden path
6. `references/troubleshooting.md` — debugging runbooks
7. `references/cookbook.md` — prompt recipes
8. Update entrypoints (SKILL.md, .cursorrules, CLAUDE.md, AGENTS.md)
9. Commit and push

---

## Verification

- Read through each file: does it give the agent enough to act without guessing?
- Test golden path manually: `antfly swarm` → MCP config → list_tables → create_table → create_index → batch → query → semantic query
- Test troubleshooting: does the runbook cover the actual error messages from the code?
- Test cookbook: ask Claude Code "add semantic search to my app" with skills loaded — does it follow the recipe?

---

## Open Questions for AJ

- Should MCP get auth before Cloud launch? Currently no auth on MCP endpoint.
- Should we add a `search_docs` MCP tool (like Supabase) to search Antfly docs at runtime?
- Zero-friction provisioning: is there a plan for `antfly.new` or similar for instant Cloud instances?
- Read-only MCP mode: worth building as a feature, or just document the workaround (restrict network access)?
