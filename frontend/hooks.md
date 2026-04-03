# React Hooks — `@antfly/components`

## useAnswerStream

Low-level hook for building custom answer/RAG UIs outside the component tree.

```typescript
import { useAnswerStream } from '@antfly/components'

const {
  answer,            // string — streamed answer text
  reasoning,         // string — agent reasoning process
  classification,    // QueryClassification — query type, route, confidence
  hits,             // QueryHit[] — retrieved documents
  followUpQuestions, // string[] — suggested follow-ups
  isStreaming,      // boolean
  error,            // Error | null
  startStream,      // (config) => Promise<void>
  stopStream,       // () => void
  reset             // () => void
} = useAnswerStream()
```

### Starting a stream

```typescript
startStream({
  url: '{{ANTFLY_API_URL}}/api/v1',
  request: {
    query: 'how does raft work',
    tables: ['docs'],
    steps: {
      generation: {
        generator: { provider: 'ollama', model: 'qwen2.5:7b' }
      }
    }
  },
  headers: { Authorization: 'ApiKey ...' }
})
```

Use `stopStream()` to cancel. Use `reset()` to clear state for a new query.

## useSearchHistory

Persists search history to localStorage.

```typescript
import { useSearchHistory } from '@antfly/components'

const {
  history,       // SearchHistoryEntry[]
  isReady,       // boolean — localStorage loaded
  saveSearch,    // (entry) => void
  clearHistory   // () => void
} = useSearchHistory(maxItems)  // pass 0 to disable
```

Each entry: `{ query, timestamp, summary?, hits?, citations? }`

## useCitations

Utilities for parsing and rendering `[resource_id X]` citations in generated answers.

```typescript
import { useCitations } from '@antfly/components'

const {
  parseCitations,      // (text) => { [resource_id]: number[] }
  highlightCitations,  // (text, hitIds) => highlighted text
  extractCitationUrls, // (answer) => string[] of cited doc IDs
  renderAsMarkdown,    // (ids, allIds) => "[1][2]"
  renderAsSequential   // (ids, allIds) => "[1, 2]"
} = useCitations()
```

Also available as standalone: `replaceCitations(text, (docId) => replacement)` for mapping citations to numbered references.

## Sharp Edges

- `useAnswerStream` is independent of the `<Antfly>` provider — you must pass URL and headers yourself
- `useSearchHistory` uses `localStorage` — not available in SSR. Check `isReady` before rendering history.
- Citations use `resource_id` format from the API — parse with `parseCitations` or `extractCitationUrls`, don't regex manually
- `stopStream()` aborts the HTTP request — the server may still process briefly. Not billed for undelivered tokens.
