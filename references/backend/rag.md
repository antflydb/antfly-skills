# RAG — Retrieval Agent, Streaming, Answer Generation

## Retrieval Agent

`POST /db/v1/agents/retrieval`

The retrieval agent is Antfly's built-in RAG pipeline. It runs multi-strategy search over declared
queries and, when configured, generates an LLM answer with streaming.

**Response shape** is chosen by the `stream` field on the request:

| `stream` | Response |
|----------|----------|
| `true` (default) | `text/event-stream` — SSE events (see below) |
| `false` | `application/json` — a `RetrievalAgentResult` |

The server reads the field as `stream orelse true`, matching the spec default: an omitted `stream`
returns SSE. Send `stream: false` for a single JSON body.

**Pipeline vs agentic mode** is chosen by `max_internal_iterations`:

| Value | Mode |
|-------|------|
| `0` (default) | Pipeline — the `queries[]` you supply are executed directly, no LLM tool-calling loop |
| `> 0` | Agentic — `queries[]` declare the available tables and indexes; how the iterations are driven depends on whether a generator is configured (below) |

Agentic mode has two drivers:

- **With a generator** (top-level `generator`/`chain`, or `steps.generation`) — an LLM tool loop. The
  model calls `build_query` and `search` (plus `navigate`, `web_search`, `fetch` when those are
  configured) for up to `max_internal_iterations` rounds, then answers. The server keeps control of
  tables, mandatory filters, indexes, and limits. The provider must support tool calling — `apple`
  does not.
- **Without a generator** — a deterministic planner (a rule function over attempt scores, not an
  LLM) refines, switches strategy, or asks for clarification.

Navigation (`tree`/`graph` agentic navigation) and web access require the LLM driver; without a
generator they are rejected.

`max_internal_iterations` must be 0–20; anything outside that range is HTTP 400.
`tools.max_tool_iterations` is also validated on 1–20 and silently lowers the effective count — the
agent runs `min(max_internal_iterations, max_tool_iterations)` iterations.

Both `query` (the natural-language string) and `queries[]` are required. Each `queries[]` entry must carry its own `table` (an entry without one is HTTP 400), plus `indexes`, `semantic_search`,
`full_text_search`, `limit`, and so on. `filter_query` / `exclusion_query` on a query entry are
mandatory predicates **for that entry only**: they are conjoined (exclusions unioned) into every
generated refinement, probe, aggregation, graph/tree traversal, and root scan derived from that
entry, and the LLM cannot weaken them. They are not table-scoped — a filter on `queries[1]` does not
constrain `queries[0]`, even when both name the same table. If you need a predicate to bind every
query, put it on every entry, or use `accumulated_filters`, which is the only global source: it is
folded into each entry's mandatory predicates before the per-entry predicates are added. A
canonical `query` on an entry contributes too: its `bool.filter` clauses are folded into that entry's
mandatory filters and its `bool.must_not` clauses into its mandatory exclusions.

### Retrieval Strategies

| Strategy | How it works |
|----------|-------------|
| `semantic` | Vector similarity search using embeddings indexes |
| `bm25` | Full-text search with BM25 scoring |
| `metadata` | Structured field queries |
| `tree` | Iterative tree navigation with summarization (PageIndex-style) |
| `graph` | Relationship-based traversal |
| `hybrid` | Combine strategies with RRF or rerank |

### Streaming (Server-Sent Events)

| Event | Payload | When |
|-------|---------|------|
| `step_started` | `SSEStepStarted` | A pipeline step began |
| `step_progress` | Step-specific object | Progress within a running step |
| `step_completed` | `AgentStep` | A pipeline step finished |
| `classification` | `ClassificationTransformationResult` | Query classification / transformation |
| `reasoning` | Text chunk | Agent's reasoning (streamed incrementally) |
| `tool_mode` | `SSEToolMode` | Tool-calling mode selected (agentic mode) |
| `context_management` | `AgentContextEvent` | Prompt context was compacted or summarized to fit the window |
| `hit` | `QueryHit` | Individual retrieved document |
| `generation` | Text chunk | Generated answer text (streamed incrementally) |
| `followup` | Question string | Suggested follow-up question |
| `eval` | `EvalResult` | Evaluation output |
| `done` | `RetrievalAgentResult` | Authoritative final envelope |
| `error` | `SSEError` | Something went wrong |

There is no `confidence` event. Confidence arrives in the `done` payload as `generation_confidence`
and `context_relevance`, and only when `steps.confidence` is configured **and** `steps.generation` is
too — a confidence step without a generation step is rejected.

`done` is the authoritative final envelope for both SSE and JSON consumers — treat streamed chunks
as progressive rendering, and `done` as the record of what actually happened.

### Answer Generation (opt-in)

Generation runs **only when `steps.generation` is configured**. With no generation step the agent is
a retrieval pipeline: it returns hits and no answer.

`GenerationStepConfig`:
- `enabled` — deprecated compatibility switch. The step runs whenever the object is present; omit
  the step (or send `enabled: false`) to turn it off
- `generator` — a `GeneratorConfig`. A generator is required once the step runs, but it does not have
  to sit on the step: the step config is satisfied by either `steps.generation.generator` or a
  top-level `request.generator`/`chain` (the step-level one wins). With neither, the request fails
  with HTTP 422
- `system_prompt` — custom system prompt for answer generation
- `generation_context` — guidance for tone, detail level, and style. It does **not** append to the
  default prompt, it replaces it: the system prompt becomes `Answer the user query using only the
  retrieved documents. <your context>`, which drops the default's cite-document-ids instruction. Set
  `system_prompt` instead when you want citations plus style guidance

`chain` (fallback across generators) is accepted when `steps.generation` is present — on the step or
at the top level. Without a generation step, a top-level `chain` is rejected with HTTP 400. `generator`
and `chain` are mutually exclusive at each level, and an empty chain is a 400.

Generator providers: `gemini`, `vertex`, `bedrock`, `anthropic`, `cloudflare`, `openai`, `chatgpt`,
`openrouter`, `ollama`, `antfly`, and `apple`. Any other provider string is HTTP 400 `invalid
retrieval agent request`. `apple` cannot drive the agentic tool loop.

Generator config is separate from embedder config — they can use different providers.

Documents enter the generation prompt as `Document N (id=<_id>): …`, with each hit's fields encoded
as TOON by default. `document_renderer` (a Handlebars template rendered per hit against
`{id, score, fields}`, e.g. `{{encodeToon this.fields}}` or `Title: {{{this.fields.title}}}`)
replaces that rendering. It requires `steps.generation`; without one, or with an invalid template, the
request is HTTP 400. On a plain `QueryRequest`, `document_renderer` is rejected.

### Citations

The default generation prompt instructs the model to cite document ids inline, and the document
context is rendered as `Document N (id=<_id>)`. So by default the model emits the document `_id`,
not a bracketed token.

The `[resource_id X]` format is the `/ai/v1/generate` contract. To get that format out of the
retrieval agent, ask for it explicitly in `steps.generation.system_prompt`.

The `@antfly/components` parser (`useCitations` hook, `replaceCitations` utility) accepts
`[resource_id X]`, `[doc_id X]`, and bare `[X]`, including comma-separated lists.

### Query Classification

Configured via `steps.classification`. Produces a `ClassificationTransformationResult`:

- `route_type` — `question` (specific factual query) or `search` (exploratory query). Two values only.
- `strategy` — `QueryStrategy`: `simple` (direct query with multi-phrase expansion), `decompose`
  (break into sub-questions), `step_back` (broader background query first), `hyde` (embed a
  hypothetical answer document)
- `semantic_mode` — `SemanticQueryMode`: `rewrite` (expanded keywords/concepts for vector search) or
  `hypothetical` (HyDE-style hypothetical answer)
- `improved_query`, `semantic_query`, plus `sub_questions` (decompose) and `step_back_query` (step_back)

Classification is **deterministic**, not model-driven: `strategy` comes from keyword heuristics over
the query string (`" and "`, `compare`, `versus` → `decompose`; `how does`, `why does`,
`architecture`, `workflow`, `background` → `step_back`; `overview`, `benefits`, `tradeoffs`,
`concept`, `summarize` → `hyde`; otherwise `simple`), and `semantic_mode` is derived from the
strategy. No LLM is called; the step schema has no `generator` or `chain`, and the server rejects
them (HTTP 400).

`force_strategy` and `force_semantic_mode` on the step config override that heuristic.

### Follow-Up Questions

Configuring `steps.followup` runs the step (`enabled` is a deprecated compatibility switch).
Follow-ups require `steps.generation`. The step schema carries only `count`; `generator`, `chain`, and
`context` are rejected (HTTP 400).

The questions themselves are **hardcoded templates** — no generator is invoked, and the generated
answer is not read. The first question is always `What else should I know about: {query}?`; any
further questions come in order from a fixed list:

1. `Which related Antfly features should I review next?`
2. `How would this change in a multi-node deployment?`
3. `What are the main operational tradeoffs here?`

`count` (default 3) must be 1–4; anything outside that range is HTTP 400.

### Evaluation

Inline evaluation is available via `steps.eval` and streams `eval` events. `eval_result` is also on
the `done` payload. Scoring is deterministic.

`evaluators` drives the step: omit it and the whole eval step is skipped; supply an empty array and
the request is rejected with HTTP 400. Two further constraints, both HTTP 400 when violated:

- `recall`, `precision`, `ndcg`, `mrr`, and `map` need `steps.eval.ground_truth.relevant_ids` to be
  non-empty
- `faithfulness`, `completeness`, `coherence`, `helpfulness`, `correctness`, and `citation_quality`
  need `steps.generation` (`relevance` and `safety` need neither)

`judge` is validated as a `GeneratorConfig` — a malformed one fails the request — but it is never
used to score anything.

## SDK Usage

**TypeScript** (`@antfly/sdk` 0.3.0) splits the two response modes into two methods:

```ts
import { AntflyClient } from "@antfly/sdk";

const client = new AntflyClient({ baseUrl: "http://localhost:8080" });

const request = {
  query: "How do I rotate API keys?",
  queries: [{ table: "docs", semantic_search: "rotate API keys", indexes: ["embeddings"], limit: 5 }],
  steps: { generation: { generator: { provider: "antfly" as const, model: "local" } } },
};

// JSON: sends stream: false, resolves to RetrievalAgentResult.
const result = await client.retrievalAgent(request);
console.log(result.generation, result.hits?.length);

// SSE: sends stream: true, resolves to an AbortController.
const controller = await client.streamRetrievalAgent(request, {
  onHit: (hit) => console.log(hit._id),
  onGeneration: (chunk) => process.stdout.write(chunk),
  onToolMode: (mode) => console.log(mode),
  onDone: (done) => console.log(done.status),
  onErrorDetail: (err) => console.error(err),
});
controller.abort();
```

Both methods take an optional third `{ signal }`. `retrievalAgent(request, callbacks)` still compiles
but is deprecated; it delegates to `streamRetrievalAgent`.

Callbacks: `onContextManagement`, `onClassification`, `onReasoning`, `onHit`, `onGeneration`,
`onConfidence`, `onFollowup`, `onEvalResult`, `onToolMode`, `onStepStarted`, `onStepProgress`,
`onStepCompleted`, `onDone`, `onErrorDetail` (typed errors, including `InferenceCapacityError` with
`retryAfterMs`), and the legacy string `onError`. `onConfidence` fires from the `done` payload when it
carries both `generation_confidence` and `context_relevance` — there is no `confidence` SSE event.

**React**: `<AnswerResults>` handles streaming automatically. `useAnswerStream` is available for
custom implementations.

## Sharp Edges

1. **SSE is the default** — omit `stream` and you get `text/event-stream`. Send `stream: false` for
   JSON (the TS SDK's `retrievalAgent()` does this for you).
2. **Generation is opt-in by presence** — without `steps.generation` there is no answer, only hits.
   Once you configure a step it runs; omit it (or send the deprecated `enabled: false`) to turn it
   off. Same for `steps.confidence` and `steps.followup`, both of which also require
   `steps.generation` — as do the generation-side evaluators in `steps.eval`.
3. **`max_internal_iterations` defaults to 0** — the default is pipeline mode. Raise it (max 20) to
   iterate: with a generator the LLM drives a tool loop, without one the deterministic planner runs.
4. **Generator config ≠ embedder config** — the LLM that generates answers is configured separately
   from the embedding model that does retrieval.
5. **Citation format is prompt-dependent** — the default prompt yields inline document ids. If you
   want `[resource_id X]` for the components parser, set `steps.generation.system_prompt`.
6. **`done` is authoritative** — reconcile streamed state against the `done` envelope rather than
   trusting accumulated chunks.
7. **Abort/cancel** — always provide a way to cancel streaming requests (AbortController in TS,
   context cancellation in Go).
8. **Current React package surface** — use `AnswerResults` for built-in answer UI; `RAGResults` is
   not part of the current exported component API.
