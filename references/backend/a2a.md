# A2A Protocol — Agent-to-Agent

## What It Is

Antfly implements Google's Agent-to-Agent (A2A) protocol, exposing Antfly as a peer agent rather than a database. Where MCP provides deterministic tools for CRUD and query execution, A2A provides skills for multi-step retrieval and query planning.

**Two things to know before you build on it:**

1. **A2A is OFF by default.** The server must be started with `--experimental`. Without it, `/a2a` and the agent card return **404**.
2. **When auth is enabled, `/a2a` requires `admin` permission.** There is no read-only A2A surface.

For most users the stable, spec'd RAG surface is the REST endpoint **`POST {{ANTFLY_API_URL}}/db/v1/agents/retrieval`** — same retrieval engine, no experimental flag, normal table-level permissions. Reach for A2A only when you specifically need the A2A protocol contract.

**Endpoints** (experimental only):

| Purpose | Path |
|---------|------|
| JSON-RPC | `{{ANTFLY_API_URL}}/a2a` — that path only; there is no `/db/v1`-prefixed alias |
| Agent card (discovery) | `{{ANTFLY_API_URL}}/.well-known/agent-card.json` |

## Agent Card

`GET /.well-known/agent-card.json`:

```json
{
  "name": "Antfly",
  "url": "/a2a",
  "version": "1.0.0",
  "protocolVersion": "0.3.0",
  "preferredTransport": "JSONRPC",
  "capabilities": { "streaming": true, "stateTransitionHistory": true },
  "defaultInputModes": ["text", "data"],
  "defaultOutputModes": ["text", "data"],
  "skills": [
    { "id": "query-builder", "name": "Query Builder", "description": "Translate natural language into Antfly query requests", "tags": ["antfly", "query"], "inputModes": ["text", "data"], "outputModes": ["text", "data"] },
    { "id": "retrieval", "name": "Retrieval", "description": "Run Antfly retrieval and generation workflows", "tags": ["antfly", "retrieval"], "inputModes": ["text", "data"], "outputModes": ["text", "data"] }
  ]
}
```

`skills` is an **array of objects**, not an array of strings. Skill selection is by `id`, read from `message.metadata.skill` first and then `params.metadata.skill`. If neither names a registered skill the dispatcher falls back to the single registered handler — but Antfly registers two, so an unnamed skill resolves to nothing. Always send the skill id.

## JSON-RPC Methods

| Method | Notes |
|--------|-------|
| `message/send` | Synchronous execution; returns the task |
| `message/stream` | Streams status + artifact update events |
| `tasks/get` | Fetch stored task state by id |
| `tasks/cancel` | Marks the task canceled in the task store |
| `agent/getAuthenticatedExtendedCard` | Card for the authenticated identity |

## Skills

### `retrieval` — RAG Agent

Runs Antfly retrieval and generation workflows.

**Modes**:
- **Pipeline** (default) — single-pass retrieval + generation
- **Agentic** — enabled when `max_internal_iterations > 0`; an iterative planner (deterministic) drives query refinement, strategy switching, and clarification. The planner is a rule function over attempt scores, not an LLM choosing tools

**Input**: message text (becomes the query) plus a data part that is **effectively required**:

| Field | Meaning |
|-------|---------|
| `table` | Table to search; builds a default full-text query from the message text |
| `limit` | Result limit for the `table`-derived default query only (default 5); ignored when you supply `queries` |
| `queries` | Explicit retrieval queries; takes precedence over `table` |
| `steps` | Explicit pipeline steps |
| `max_internal_iterations` | > 0 switches to agentic mode |

The adapter only forwards `queries[]` when the data part supplies `queries` or `table`. With
neither, the retrieval request goes out with no `queries` key at all, which the retrieval agent
rejects as an invalid request — the task ends `failed` with "invalid retrieval agent request". Send
one or the other on every call.

**Output**: streamed A2A artifact updates. Each retrieval event becomes an artifact **named after the event**; the `done` event becomes the artifact named `result`. The artifact payload is not the raw event — it is wrapped as `{"event": "<event name>", "data": <event payload>}`, so `result` carries the `RetrievalAgentResult` under `data`.

**Status states**: emits `working` at start. The terminal state is the `done` payload's `status` field verbatim, defaulting to `completed` when the payload carries no status — in practice `completed`, `clarification_required`, or `incomplete`, the three the retrieval agent produces. `failed` comes from the adapter's error branch instead (an `error` event, or a rejected/unauthorized request), and `in_progress` is never emitted.

### `query-builder` — Natural Language to QueryRequest

Translates natural language intent into an Antfly `QueryRequest`.

**Input**: message text (the intent) plus an optional data part with `table`. A `context` key is forwarded but then silently discarded — it is not part of `QueryBuilderRequest`. `table` is the only field the adapter carries through; everything else the request accepts — `constraints`, `example_documents`, `schema_fields`, `session_id`, `decisions`, `mode`, `output`, `generator`, `max_internal_iterations`, `max_user_clarifications` — is reachable only through `POST /db/v1/agents/query-builder`.

**Output**: one artifact named `query`, carrying the entire `QueryBuilderResult` — not just the query. That is the mandatory `query` (the native Bleve query object), the optional `query_request` and `retrieval_query_request` (an executable `QueryRequest`, and its retrieval-agent counterpart when tree/graph features are involved), plus `session_id`, `iteration`, `clarification_count`, `status`, `steps`, `remaining_internal_iterations`, `remaining_user_clarifications`, `questions`, `specialist`, `plan`, `explanation`, `confidence`, and `warnings`.

**An LLM is optional.** With no generator configured, Antfly builds the query with a deterministic full-text/filter builder — **silently**. No warning is emitted for that path: the fallback warning fires only when a generator *was* requested and no generation runner was available, or when generator-backed building was attempted and failed. `warnings` is omitted from the result entirely when nothing was collected, so its absence tells you nothing about whether a model was involved.

## When to Use MCP vs. A2A vs. REST

| Need | Use |
|------|-----|
| Create/drop tables and indexes | MCP |
| Insert/delete/transform documents | MCP (`batch`) |
| Any query, simple through hybrid | MCP (`query`) |
| RAG with streaming answers | REST `POST /db/v1/agents/retrieval` (stable) |
| RAG inside an A2A agent mesh | A2A `retrieval` (experimental + admin) |
| Natural language → QueryRequest | REST `POST /db/v1/agents/query-builder`, MCP `describe_query_request` + `query`, or A2A `query-builder` |
| Multi-turn clarification loops | A2A `retrieval` in agentic mode |

## Sharp Edges

1. **404 unless `--experimental`** — `/a2a` and `/.well-known/agent-card.json` both return 404 on a default server. This is the first thing to check. Neither path has a `/db/v1`-prefixed alias: those routes are intentionally never registered and return 404 even with the flag on.
2. **Admin-only, and 403 is not 404** — with auth enabled, `/a2a` requires admin permission and a non-admin identity gets **403 `{"error":"forbidden"}`**. A **404** means the opposite problem: the server was started without `--experimental`, so the route was never registered. Distinguish them before debugging credentials. The agent card is not admin-gated — it is served to any caller once the flag is on, so a read-only identity can still fetch it.
3. **The card is at `/.well-known/agent-card.json`**, not `agent.json`. The older path returns 404 even with `--experimental` on.
4. **`skills` is an array of objects** — parse `skill.id`, don't treat the entries as strings.
5. **`tasks/cancel` marks, it doesn't interrupt** — the task is recorded as canceled in the task store, but in-flight synchronous work is not aborted.
6. **Agentic mode does not need a generator** — `max_internal_iterations > 0` is gated only by the tool policy: the request is rejected if no declared query is allowed by it. Generation remains separately opt-in via `steps.generation`.
7. **Streaming is A2A event framing**, not the REST retrieval SSE shape — artifact-update and status-update events, not raw retrieval events.
