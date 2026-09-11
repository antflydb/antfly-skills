# React Hooks — `@antfly/components`

## useAnswerStream

Low-level hook for a single streamed answer, outside the component tree.

```typescript
import { useAnswerStream } from '@antfly/components'

const {
  answer,            // string — streamed answer text
  reasoning,         // string — agent reasoning
  classification,    // QueryClassification | null — route_type, improved_query, semantic_query, confidence
  hits,              // QueryHit[] — retrieved documents
  followUpQuestions, // string[]
  isStreaming,       // boolean
  error,             // Error | null
  startStream,       // ({ url, request, headers? }) => Promise<void>
  stopStream,        // () => void
  reset              // () => void
} = useAnswerStream()
```

### Starting a stream

```typescript
startStream({
  url: '{{ANTFLY_API_URL}}',
  request: {
    query: 'how does raft work',
    generator: { provider: 'ollama', model: 'qwen2.5:7b' },
    queries: [{ table: 'docs', semantic_search: 'how does raft work', indexes: ['emb'], limit: 10 }],
    steps: { generation: { enabled: true } }
  },
  headers: { Authorization: 'ApiKey ...' }
})
```

`request` is a `RetrievalAgentRequest`: `query` and `queries` are required. `stream` is not read from your request — it is overwritten from the set of wired callbacks, and this hook always wires streaming callbacks, so it always sends `stream: true`. `startStream` resets state and aborts any in-flight stream. Use `stopStream()` to cancel, `reset()` to clear state.

The hook wires only the SSE callbacks (`onClassification`, `onHit`, `onReasoning`, `onGeneration`, `onFollowup`, `onComplete`, `onError`), which is why it carries no confidence, eval, or step state. A plain JSON (non-SSE) response routes instead to `onRetrievalAgentResult`, which the hook leaves unwired: `isStreaming` flips back to false and `answer` stays empty, with no error.

## useChatStream

Multi-turn version. Each `sendMessage` appends a `ChatTurn` and streams into it; full history is sent to the agent.

```typescript
import { useChatStream } from '@antfly/components'

const { turns, isStreaming, sendMessage, abort, reset } = useChatStream()

sendMessage('how does raft work', {
  url: '{{ANTFLY_API_URL}}',
  table: 'docs',
  headers: { Authorization: 'ApiKey ...' },
  generator: { provider: 'openai', model: 'gpt-4o' },
  semanticIndexes: ['emb'],
  maxInternalIterations: 5   // 1+ = agentic tool calling; omit or pass 0 (dropped from the request) for pipeline mode
})
```

`ChatConfig` also takes `agentKnowledge`, `systemPrompt`, `followUpCount`, `limit`, `steps`, `tools`, `fields`, `filterQuery`, `exclusionQuery`. Every `ChatTurn` carries `id`, `userMessage`, `assistantMessage`, `hits`, `followUpQuestions`, `classification`, `confidence`, `clarification`, `appliedFilters`, `reasoningText`, `steps`, `activeSteps`, `toolCallsMade`, `error`, `isStreaming`.

`<ChatBar>` wraps this hook and injects `url`/`headers`/`table` from the provider.

## useSearchHistory

Persists search results to `localStorage` under the key `antfly-search-history`.

```typescript
import { useSearchHistory } from '@antfly/components'

const {
  history,      // SearchResult[]
  isReady,      // boolean — always true
  upsertSearch, // (result: SearchResult) => void
  saveSearch,   // alias of upsertSearch
  clearHistory  // () => void
} = useSearchHistory(10)  // maxResults, default 10; pass 0 to disable writes
```

`SearchResult` is `{ id, query, timestamp, hits, summary?, citations? }` — `hits` is required (`QueryHit[]`), `citations` is `{ id, quote?, score? }[]`. Entries are keyed by `id`: re-upserting the same id replaces it and moves it to the front, then the list is truncated to `maxResults`.

## useCitations

Wrapper around the standalone citation utilities. Citations are `[resource_id 1, 2]`, `[doc_id 1]`, or bare `[1, 2]`.

```typescript
import { useCitations } from '@antfly/components'

const {
  parseCitations,      // (text) => Citation[]
  highlightCitations,  // (text, options: CitationRenderOptions) => string
  extractCitationUrls, // (text) => string[] of cited resource IDs
  renderAsMarkdown,    // (ids) => "[[1]](#hit-1), [[2]](#hit-2)"
  renderAsSequential   // (ids, allIds) => "[[1]](#hit-5), [[2]](#hit-7)"
} = useCitations()
```

Standalone equivalents (no hook required): `parseCitations`, `replaceCitations`, `renderAsMarkdownLinks`, `renderAsSequentialLinks`, `getCitedResourceIds`.

```typescript
import { replaceCitations, renderAsSequentialLinks, getCitedResourceIds } from '@antfly/components'

// options is an OBJECT with a renderCitation function
const rendered = replaceCitations(answer, { renderCitation: renderAsSequentialLinks })

const grouped = replaceCitations(answer, {
  renderCitation: (ids, allIds) => `[${ids.map((id) => allIds.indexOf(id) + 1).join(',')}]`
})

const citedIds = getCitedResourceIds(answer)          // unique IDs, first-appearance order
const citedHits = hits.filter((h) => citedIds.includes(h._id))
```

`Citation` is `{ originalText, ids, startIndex, endIndex }`. `getCitedDocumentIds` is a deprecated alias of `getCitedResourceIds`.

## Context Hooks

| Hook | Must be inside | Gives you |
|------|----------------|-----------|
| `useAnswerResultsContext()` | `<AnswerResults>` | `query`, `answer`, `reasoning`, `hits`, `classification`, `followUpQuestions`, `confidence`, `evalResult`, `result`, `isStreaming`, `agentKnowledge` |
| `useAutosuggestContext()` | `<Autosuggest>` | `query`, `results`, `facetData`, `selectedIndex`, `handleSelect`, `isLoading`, `registerItem`, `unregisterItem`, `fields` |
| `useChatContext()` | `<ChatBar>` | `turns`, `isStreaming`, `sendMessage`, `sendFollowUp`, `respondToClarification`, `abort`, `reset`, `config` |

Each throws when used outside its component.

## Sharp Edges

- `useAnswerStream` and `useChatStream` are independent of the `<Antfly>` provider — you pass `url` and `headers` yourself
- `useSearchHistory` reads `localStorage` in a lazy initializer and guards `typeof window`, so it is SSR-safe; `isReady` is hardcoded `true` and is not a loading signal
- `replaceCitations(text, options)` takes an options **object** (`{ renderCitation }`), not a bare function
- Citations use the `resource_id` format from the API — parse with `parseCitations` / `getCitedResourceIds` rather than hand-rolled regexes; the matcher also swallows any other `[...]` bracket text
- `stopStream()` / `abort()` aborts the HTTP request; the server may keep working briefly
