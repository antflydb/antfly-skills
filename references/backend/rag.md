# RAG — Retrieval Agent, Streaming, Answer Generation

## Retrieval Agent

`POST /db/v1/agents/retrieval`

The retrieval agent is Antfly's built-in RAG pipeline. It runs multi-strategy search over declared
queries and, when configured, generates an LLM answer with streaming.

**Response shape** is chosen by the `stream` field on the request:

| `stream` | Response |
|----------|----------|
| `true` | `text/event-stream` — SSE events (see below) |
| `false` (default) | `application/json` — a `RetrievalAgentResult` |

The spec declares `default: true`, but the server reads the field as `stream orelse false`, so an
omitted `stream` returns JSON. Ask for SSE explicitly with `stream: true`.

**Pipeline vs agentic mode** is chosen by `max_internal_iterations`:

| Value | Mode |
|-------|------|
| `0` (default) | Pipeline — the `queries[]` you supply are executed directly, no LLM tool-calling loop |
| `> 0` | Agentic — an iterative planner (deterministic rule function over attempt scores, not an LLM) refines, switches strategy, or asks for clarification; `queries[]` declare the available tables and indexes |

Only a negative `max_internal_iterations` is rejected (HTTP 400); values above 20 are accepted. The
1–20 bound belongs to `tools.max_tool_iterations`, which is validated on that range and then
silently lowers the effective count — the agent runs `min(max_internal_iterations,
max_tool_iterations)` iterations.

Both `query` (the natural-language string) and `queries[]` are required. Each `queries[]` entry carries its own `table`, plus `indexes`, `semantic_search`,
`full_text_search`, `limit`, and so on. `filter_query` / `exclusion_query` on a query entry are
mandatory predicates **for that entry only**: they are conjoined (exclusions unioned) into every
generated refinement, probe, aggregation, graph/tree traversal, and root scan derived from that
entry, and the LLM cannot weaken them. They are not table-scoped — a filter on `queries[1]` does not
constrain `queries[0]`, even when both name the same table. If you need a predicate to bind every
query, put it on every entry, or use `accumulated_filters`, which is the only global source: it is
folded into each entry's mandatory predicates before the per-entry predicates are added.

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
- `enabled` — the spec's default is `false`, but the server does not behave that way: configuring
  `steps.generation` at all runs the step unless you set `enabled: false` explicitly
- `generator` — a `GeneratorConfig`. A generator is required once the step runs, but it does not have
  to sit on the step: the step config is satisfied by either `steps.generation.generator` or a
  top-level `request.generator` (the step-level one wins). With neither, the request is rejected
- `system_prompt` — custom system prompt for answer generation
- `generation_context` — guidance for tone, detail level, and style. It does **not** append to the
  default prompt, it replaces it: the system prompt becomes `Answer the user query using only the
  retrieved documents. <your context>`, which drops the default's cite-document-ids instruction. Set
  `system_prompt` instead when you want citations plus style guidance

`chain` is **rejected** on the retrieval agent — both `steps.generation.chain` and the top-level
`chain` return HTTP 400 `invalid retrieval agent request`. Chain fallback is declared in the spec but
not implemented here; configure a single `generator`.

Generator providers: the retrieval agent accepts only `gemini`, `vertex`, `openai`, `ollama`, and
`antfly`. `anthropic`, `bedrock`, `cohere`, `openrouter`, and `mock` are in the API enum and parse
against the schema, but config conversion has no branch for them and rejects the request with HTTP
400 `invalid retrieval agent request`.

Generator config is separate from embedder config — they can use different providers.

`document_renderer` (a handlebars template, e.g. `{{encodeToon this.fields}}`) is a **QueryRequest**
field. On a retrieval-agent request it is rejected unconditionally with HTTP 400, with or without
`steps.generation`.

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
strategy. No LLM is called — `steps.classification.generator` and `steps.classification.chain` are
**rejected** with HTTP 400.

`force_strategy` and `force_semantic_mode` on the step config override that heuristic.

### Follow-Up Questions

Configuring `steps.followup` runs the step unless you set `enabled: false` explicitly — the spec's
`false` default does not apply. Follow-ups require `steps.generation`. `generator` and `chain` on the
followup step are **rejected** (HTTP 400).

The questions themselves are **hardcoded templates** — no generator is invoked, and the generated
answer is not read. The first question is always `What else should I know about: {query}?`; any
further questions come in order from a fixed list:

1. `Which related Antfly features should I review next?`
2. `How would this change in a multi-node deployment?`
3. `What are the main operational tradeoffs here?`

`count` (default 3) clamps to 1–4, so four questions is the ceiling regardless of the spec's maximum
of 10. `context` is accepted by the schema and ignored by the server.

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

**TypeScript** (`@antfly/sdk` 0.0.14):
```
client.retrievalAgent(request, callbacks)
  → Promise<RetrievalAgentResult | AbortController>
```
The `AbortController` is returned only in streaming mode; a JSON (`stream: false`) response resolves
to the `RetrievalAgentResult`. Callers must narrow the union.

Callbacks: `onClassification`, `onReasoning`, `onHit`, `onGeneration`, `onConfidence`, `onFollowup`,
`onEvalResult`, `onFilterApplied`, `onSearchExecuted`, `onStepStarted`, `onStepProgress`,
`onStepCompleted`, `onDone`, `onError`.

The list is wider than the wire. `onConfidence`, `onFilterApplied`, and `onSearchExecuted` are dead:
the server emits no `confidence`, `filter_applied`, or `search_executed` event, so they never fire
(confidence still arrives on `done`, as above). The gap runs the other way too — the server emits
`tool_mode` in agentic mode and the SDK has no callback for it, so read it from `done`'s steps or
parse the stream yourself.

**React**: `<AnswerResults>` handles streaming automatically. `useAnswerStream` is available for
custom implementations.

## Sharp Edges

1. **JSON is the default, not SSE** — the spec says `stream` defaults to `true`, but the server
   applies `false`. Omit the field and you get `application/json`; a client that expects a stream
   must set `stream: true`.
2. **Generation is opt-in, but `enabled` is not the switch** — without `steps.generation` there is no
   answer, only hits. Once you configure a step it runs; `enabled: false` is the only way to turn it
   off. Same for `steps.confidence` and `steps.followup`, both of which also require
   `steps.generation` — as do the generation-side evaluators in `steps.eval`.
3. **`max_internal_iterations` defaults to 0** — the default is pipeline mode. Raise it to let the
   planner iterate; it does not need a generator to do so.
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
