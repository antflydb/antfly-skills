# RAG — Retrieval Agent, Streaming, Answer Generation

## Retrieval Agent

`POST /api/v1/agents/retrieval`

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

The retrieval agent streams results via SSE. Common event types:

| Event | Payload | When |
|-------|---------|------|
| `classification` | Classification object | Query classification / routing |
| `reasoning` | Text chunk | Agent's reasoning process (streamed incrementally) |
| `hit` | Document hit | Individual retrieved document |
| `generation` / `answer` | Text chunk | Generated answer text (streamed incrementally) |
| `followup` / `followup_question` | Question string | Suggested follow-up question |
| `confidence` | Score data | Answer confidence score |
| `eval` | Eval result | Optional evaluation output |
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

Inline evaluation is available via the retrieval agent `steps.eval` config and streams `eval` events.

## SDK Usage

**TypeScript**:
```
client.retrievalAgent(request, {
  onClassification, onReasoning, onHit, onAnswer, onFollowUpQuestion, onDone
})
```
Returns an `AbortController` for cancellation.

**React**: `<AnswerResults>` handles streaming automatically. `useAnswerStream` hook is available for custom implementations.

## Sharp Edges

1. **Streaming requires SSE handling** — responses are `text/event-stream`, not JSON. SDKs handle this, but raw HTTP clients need SSE parsing.
2. **Generator config ≠ embedder config** — the LLM that generates answers is configured separately from the embedding model that does retrieval.
3. **Citations use `resource_id`** — this may differ from the document `_id` in some cases. Parse carefully.
4. **Follow-up questions are best-effort** — quality depends on the LLM model. Smaller models produce weaker follow-ups.
5. **Abort/cancel** — always provide a way to cancel streaming requests (AbortController in TS, context cancellation in Go).
6. **Current React package surface** — use `AnswerResults` for built-in answer UI; `RAGResults` is not part of the current exported component API.
