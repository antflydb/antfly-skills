# Plan: antfly-skills v2 — Agent Operability

## Context

antfly-skills v1 teaches an AI agent **what Antfly is**. Codex's comparison against Supabase/Neon revealed the gap: we don't teach agents **how to safely connect, inspect, scaffold, verify, debug, and evolve** an Antfly deployment. This plan closes that gap.

**What exists today** (already shipped in antfly-skills repo):
- one skill with three reference domains (backend, frontend, ops), concept docs, and sharp edges
- MCP + A2A protocol documentation (tools, setup snippets)
- SKILL.md, CLAUDE.md, .cursorrules, AGENTS.md entrypoints

**What's missing** (Codex's priority list, filtered to what we can build now):

| # | Item | New file |
|---|------|----------|
| 1 | MCP/A2A client setup recipes (every IDE, copy-paste) | `references/backend/mcp-setup.md` |
| 2 | Capability matrix (exact tool/action catalog) | `references/backend/capabilities.md` (exists — expand) |
| 3 | Safe operating modes + prod guardrails | `references/backend/safety.md` |
| 4 | Golden path (setup → first semantic query → first RAG) | `references/getting-started.md` |
| 5 | Environment contract (config/flag template, all vars) | `references/ops/environment.md` |
| 6 | Troubleshooting runbooks | `references/troubleshooting.md` |
| 10 | Prompt cookbook ("when user asks X, do Y") | `references/cookbook.md` |

Items 7 (change management), 8 (introspection/codegen), 9 (starter templates) are deferred — they need product features or AJ input.

---

## New Files

### `references/backend/mcp-setup.md` — Copy-Paste MCP/A2A Config for Every IDE

Expand the current mcp.md setup section into a complete recipe file with:

- **Claude Code**: `claude mcp add --transport http antfly <url>` recipe plus the project `.mcp.json` shape and its placeholder caveats
- **Cursor**: `.cursor/mcp.json` config
- **Codex / other**: generic MCP client config
- **Local dev**: `http://localhost:8080/mcp/v1` with `antfly standalone`
- **Antfly Cloud**: `https://platform.antfly.io/cloud/v1/{INSTANCE_ID}/mcp/v1` with `Authorization: Bearer <instance API key>`
- **A2A setup**: how to point an A2A-compatible agent at `/.well-known/agent-card.json` (requires the server to run with `--experimental`)
- **Verify connection**: step-by-step — call `describe_mcp_capabilities`, then `list_tables`, expect success

~200 lines.

### `references/backend/capabilities.md` — Exact Capability Matrix

A single dense table an agent can scan to know exactly what's possible:

**MCP Tools** (16 built-in, plus dynamically registered extension tools): the read/discovery surface (`describe_mcp_capabilities`, `describe_query_request`, `list_tables`, `describe_table`, `list_indexes`, `describe_indexes`, `get_document`, `sample_documents`, `query`), the write surface (`batch` — inserts, deletes, and `$set`-style transforms), and the admin surface (`create_table`, `drop_table`, `create_index` — embeddings indexes only — `drop_index`, `backup`, `restore` — the last two require `tableName`, `backupId`, `location`, **and `connection`**). Each tool carries a permission tier (none/read/write/admin) and is filtered per identity.

**A2A Skills** (2):
| Skill | Action | Streaming? |
|-------|--------|-----------|
| `retrieval` | RAG: multi-strategy search + LLM answer | Yes |
| `query-builder` | Natural language → Antfly QueryRequest | Yes |

**REST API** (not available via MCP):
| Action | Endpoint | Why not in MCP |
|--------|----------|---------------|
| Linear merge (bulk import) | `POST /db/v1/tables/{tableName}/merge` | Complex cursor workflow |
| Transactions | `POST /db/v1/transactions/*`, cross-table `POST /db/v1/batch` | Multi-table atomic / OCC read_set |
| User management | `/auth/v1/users/*` | Auth/admin scope |

~150 lines.

### `references/backend/safety.md` — Safe Operating Modes & Guardrails

Critical file. Based on actual code analysis:

**Current state**: with auth enabled, the MCP server authorizes every request and enforces a per-tool permission tier (none/read/write/admin); tools are filtered from `tools/list` and re-checked per call, so a read-only key yields a read-only MCP surface. A default local server without auth is unrestricted — treat localhost-only as the boundary there. The guardrails to document are about **credential scoping**, not compensating for missing auth.

Content:
- **Scope the key to the job** — give agents an instance-scoped read-only key for retrieval work; reserve write/admin keys for explicit provisioning tasks.
- **Dangerous actions list**: `drop_table`, `drop_index`, `batch` with deletes, `restore` (overwrites data). Agent should confirm with user before executing these even when the key allows them.
- **Safe actions**: the describe/list/sample/query tools and `backup` — read-only or non-destructive.
- **Local dev default**: Assume `antfly standalone` on localhost unless told otherwise. Don't point at production without explicit user confirmation.
- **Prod guardrails**: use scoped keys per environment; don't hand an admin key to a general-purpose agent.
- **Approval-required operations**:
  - Dropping tables or indexes
  - Batch deletes
  - Restoring from backup
  - Creating indexes (blocks while validating the embedder with a live probe)

~200 lines.

### `references/getting-started.md` — Golden Path (Setup to First Success)

A deterministic bootstrap workflow an agent can follow:

**Step 1: Start Antfly**
```bash
antfly standalone
```
Verify: `curl http://localhost:4200/readyz` → ready

**Step 2: Configure MCP** (copy-paste config for IDE of choice — link to mcp-setup.md)

**Step 3: Verify connection**
MCP: `describe_mcp_capabilities`, then `list_tables` → expect empty array

**Step 4: Create a table**
MCP: `create_table` with tableName="demo" — note `fields` is a JSON-encoded TableSchema string (`document_schemas` with JSON Schema properties); a flat name→type map is silently ignored and yields an empty schema

**Step 5: Create an embeddings index**
MCP: `create_index` with embedder config (ollama + nomic-embed-text, the local `antfly` provider, or openai for cloud)
Note: blocks while validating the embedder with a live probe.

**Step 6: Insert a document**
MCP: `batch` with inserts: `{ "doc-1": { "title": "Hello", "content": "This is a test document", "category": "test" } }`

**Step 7: Run a full-text search**
MCP: `query` with fullTextSearch: `"title:Hello"`, tableName: "demo"

**Step 8: Run a semantic search**
MCP: `query` with semanticSearch: "greeting", indexes: ["your_index_name"], tableName: "demo"
Important: must specify `indexes` — omitting it is rejected with HTTP 422.

**Step 9: Run a retrieval agent request**
`POST /db/v1/agents/retrieval` with query + table + generator config (or the A2A `retrieval` skill on an `--experimental` server)

**Step 10: Validate health**
`curl http://localhost:4200/readyz` → ready
`curl http://localhost:4200/metrics` → Prometheus metrics

~250 lines.

### `references/ops/environment.md` — Environment Contract

Canonical configuration surface — flags, config keys, and the env vars that actually exist:

```
# Server flags (antfly standalone)
--id 1                       # node id
--host 127.0.0.1 --port 8080 # public API
--health-port 4200           # /healthz, /readyz, /metrics
--config /etc/antfly/config.json   # JSON config (type-checked; unknown top-level keys ignored)
--data-dir ~/.antfly         # storage root
--secret-store-path <file>   # repeatable; plaintext JSON secret store

# Config keys (JSON)
log: { level: info|debug|warn|error, style: logfmt|terminal|json|noop }
inference: { api_url: ... }  # external inference server, optional
storage: { engine: lite|local|object, ... }
cors: { enabled, allowed_origins }

# Environment variables
ANTFLY_SECRET_STORE_PATH=    # read by `antfly serverless` only; other runtimes use the flag
ANTFLY_INFERENCE_MODELS_DIR= # model cache (default ~/.antfly/inference/models)

# Model provider keys (resolved as ${secret:openai.api_key} → OPENAI_API_KEY, etc.)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
COHERE_API_KEY=

# S3 storage (serverless/object engine; prefer credentials.source default/web_identity)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```

Plus: standalone vs distributed vs serverless assumptions, where inference lives, where logs/metrics are.

~150 lines.

### `references/troubleshooting.md` — Debugging Runbooks

Structured as: **Symptom → Cause → Fix**

**Semantic search fails or returns nothing**
- Missing `indexes` parameter (most common) — the server returns HTTP 422; add `indexes: ["your_index_name"]`
- Embeddings not ready yet — use `sync_level: "full_index"` on writes, or wait for enrichment
- Wrong index name — check with `list_indexes`
- Empty table — verify data was inserted

**Embeddings not generating / index creation hangs**
- Local inference model not downloaded — run `antfly inference pull --variants i8 BAAI/bge-small-en-v1.5`
- Embedder validation probe failing — invalid config is a 400; an unreachable provider is a 503
- Dimension mismatch — a declared dimension that disagrees with a successful probe is a 400; `validation: "defer_probe"` only tolerates an unreachable/transiently failing probe (falling back to the declared dimension), it does not rescue a genuine mismatch

**Retrieval agent / streaming fails**
- Generator not configured — provide `generator: { provider, model }` in request (generation only runs when `steps.generation` is set)
- Streaming requires `stream: true` — the server's default response is JSON; SSE clients must opt in
- A2A endpoint is `/a2a` (JSON-RPC, `--experimental` only), REST endpoint is `/db/v1/agents/retrieval` (SSE) — don't mix them

**Auth failures**
- API key format wrong — must be `ApiKey base64(keyID:keySecret)`, not just the secret
- Key expired or deleted — create new key, secret only shown once
- MCP tools missing from `tools/list` — the key's permission tier hides them; use a key with the needed scope

**Inference / model issues**
- "model not found" — run `antfly inference list` to see downloaded models
- Slow first request — model loads on demand, first inference is slow
- CPU inference slow for large models — use `i8` quantized variants

**Cluster / storage issues**
- Quorum — metadata node count must be odd (any odd count ≥ 1) and is immutable after cluster creation
- Shard not found — table may not have finished creating, check with `list_tables`
- S3 bucket missing — set `bucket_provisioning: create_if_missing` or create it up front
- `/healthz` and `/readyz` are served on both the API port and the health port (4200); `/metrics` is health-port-only

~300 lines.

### `references/cookbook.md` — Prompt Cookbook

"When the user asks X, do Y" — concrete agent recipes.

**"Add semantic search to my app"**
1. Read `references/backend/indexes.md` for embeddings config
2. Check if table exists (MCP: `list_tables`)
3. Create embeddings index with appropriate template + provider
4. If data already exists, run the reprocess API (`reprocess-jobs`, per-document reprocess, or `antfly artifact reprocess`) — newly admitted indexes also trigger a corpus-wide backfill
5. Update queries to include `semantic_search` + `indexes` parameter
6. For UI: add `semanticIndexes` prop to `<Results>` or use `<AnswerResults>`

**"Set up local Antfly"**
1. `antfly standalone` (or `docker run ... standalone`)
2. Verify: `curl localhost:4200/readyz`
3. Configure MCP in IDE (link to mcp-setup.md)
4. Follow golden path (link to getting-started.md)

**"Debug empty search results"**
1. Check `indexes` parameter present for semantic search (missing → HTTP 422)
2. MCP: `list_indexes` — verify index exists and is healthy
3. MCP: `list_tables` / `sample_documents` — verify table has data
4. Try full-text search first (simpler) to isolate vector vs query issues
5. Check sync_level — data may not be indexed yet

**"Create MCP config"**
1. Determine environment (local standalone vs cloud)
2. Generate IDE-specific config (link to mcp-setup.md)
3. Test with `describe_mcp_capabilities` + `list_tables`

**"Wire retrieval agent / A2A flow"**
1. Read `references/backend/rag.md` (REST) or `references/backend/a2a.md` (experimental)
2. Ensure table has embeddings index
3. Choose mode: pipeline (simple) or agentic (multi-turn)
4. Configure generator (provider + model)
5. Handle streaming events (singular `hit` and `followup` frames; only `done`-last is guaranteed): classification, reasoning, hit, generation, followup, done

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
4. For existing data: use the bounded reprocess API (reprocess-jobs / per-document reprocess), not touch-and-re-insert
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
│   ├── capabilities.md         # exact tool/action matrix
│   └── safety.md               # NEW: safe operating modes, guardrails
├── frontend/
│   └── (existing files...)
└── ops/
    ├── (existing files...)
    └── environment.md           # NEW: canonical config/env contract
```

Estimated ~1,550 lines total.

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
4. `references/ops/environment.md` — config/env contract
5. `references/getting-started.md` — golden path
6. `references/troubleshooting.md` — debugging runbooks
7. `references/cookbook.md` — prompt recipes
8. Update entrypoints (SKILL.md, .cursorrules, CLAUDE.md, AGENTS.md)
9. Commit and push

---

## Verification

- Read through each file: does it give the agent enough to act without guessing?
- Test golden path manually: `antfly standalone` → MCP config → list_tables → create_table → create_index → batch → query → semantic query
- Test troubleshooting: does the runbook cover the actual error messages from the code?
- Test cookbook: ask Claude Code "add semantic search to my app" with skills loaded — does it follow the recipe?
- Run `node tools/verify-references.mjs` with `ANTFLY_OPENAPI` pointing at a current antfly checkout before every merge.

---

## Open Questions for AJ

- Cloud key UX: should the dashboard's API-key screen offer the copy-paste MCP snippet + skills install prompt at creation time?
- Should we add a `search_docs` MCP tool (like Supabase) to search Antfly docs at runtime?
- Zero-friction provisioning: is there a plan for `antfly.new` or similar for instant Cloud instances?
- Per-tool approval hints: MCP already filters tools by key scope — do we also want the skill to declare which allowed tools an agent should confirm with the user before calling (drops, deletes, restore)?
