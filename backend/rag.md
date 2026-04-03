# RAG — Retrieval Agent, Streaming, Answer Generation

## Retrieval Agent

`POST /api/v1/retrieval-agent`

The retrieval agent is Antfly's built-in RAG pipeline. It runs multi-strategy search, retrieves relevant documents, and optionally generates an LLM answer with streaming.

### Retrieval Strategies

The agent can use multiple search strategies in a single request:

| Strategy | How it works |
|----------|-------------|
| `semantic` | Vector similarity search using embeddings indexes |
| `bm25` | Full-text keyword search |
| `metadata` | Filter-based retrieval on structured fields |
| `tree` | Hierarchical document traversal |
| `graph` | Graph traversal across document edges |
| `hybrid` | Combined BM25 + semantic with RRF merge |

### Streaming (Server-Sent Events)

The retrieval agent streams results via SSE. Event types:

| Event | Payload | When |
|-------|---------|------|
| `step_started` | Step name | Pipeline step begins |
| `step_progress` | Progress data | Progress within a step |
| `step_completed` | Step result | Step finishes |
| `reasoning` | Text chunk | Agent's reasoning process (streamed incrementally) |
| `hit` | Document hit | Individual retrieved document |
| `generation` | Text chunk | Generated answer text (streamed incrementally) |
| `followup` | Question string | Suggested follow-up question |
| `confidence` | Score data | Answer confidence score |
| `done` | — | Pipeline complete |
| `error` | Error message | Something went wrong |

### Answer Generation

The agent can generate an LLM-powered answer from retrieved documents. Configure with:

- **Provider**: `ollama`, `openai`, `anthropic`, `bedrock`, `google`
- **Model**: provider-specific model name
- **System prompt**: custom instructions for the LLM
- **Generation context**: additional context injected into the prompt

Generator config is separate from embedder config — they can use different providers.

### Citations

Generated answers include citations in `[resource_id X]` format, where X maps to the `_id` of a retrieved document. Parse these to link answers back to source documents.

The `@antfly/components` package provides `useCitations` hook and `replaceCitations` utility for rendering citations in the frontend.

### Query Classification

The agent classifies incoming queries by type:
- **Factual** — looking for a specific answer
- **Exploratory** — browsing/researching a topic
- **Navigational** — looking for a specific resource

Classification can be used to route queries or adjust UI behavior.

### Follow-Up Questions

The agent auto-generates suggested follow-up questions based on the query and retrieved context. Useful for conversational interfaces.

### Evaluation

`POST /api/v1/eval` — evaluate retrieval quality.

Metrics: `recall`, `precision`, `ndcg`, `mrr`

Provide ground truth (`relevant_ids`) and retrieved results (`retrieved_ids`) to measure search quality.

## SDK Usage

**TypeScript**:
```
client.agents.retrieval(request, {
  onClassification, onReasoning, onHit, onGeneration, onFollowup, onComplete
})
```
Returns an `AbortController` for cancellation.

**React**: `<AnswerResults>` and `<RAGResults>` components handle streaming automatically. `useAnswerStream` hook for custom implementations.

## Sharp Edges

1. **Streaming requires SSE handling** — responses are `text/event-stream`, not JSON. SDKs handle this, but raw HTTP clients need SSE parsing.
2. **Generator config ≠ embedder config** — the LLM that generates answers is configured separately from the embedding model that does retrieval.
3. **Citations use `resource_id`** — this may differ from the document `_id` in some cases. Parse carefully.
4. **Follow-up questions are best-effort** — quality depends on the LLM model. Smaller models produce weaker follow-ups.
5. **Abort/cancel** — always provide a way to cancel streaming requests (AbortController in TS, context cancellation in Go).
