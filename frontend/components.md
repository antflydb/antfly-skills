# React Components — `@antfly/components`

## Installation

```
npm install @antfly/components @antfly/sdk react react-dom
```

Import stylesheet (required): `import '@antfly/components/dist/components.css'`

## Component Reference

### `<Antfly>` — Root Provider

**Required.** All other components must be descendants.

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `url` | string | yes | Antfly API base URL |
| `table` | string | yes | Default table for all child components |
| `headers` | object | no | Custom headers (auth, etc.) |
| `onChange` | function | no | Callback when search state changes |

### `<QueryBox>` — Search Input

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `id` | string | yes | Unique ID (referenced by Results via `searchBoxId`) |
| `mode` | `"live"` \| `"submit"` | yes | `live` = search as you type; `submit` = on enter/button |
| `placeholder` | string | no | Input placeholder text |
| `buttonLabel` | string | no | Submit button text (submit mode only) |
| `initialValue` | string | no | Pre-filled value |
| `onInputChange` | function | no | Callback on input change |
| `onSubmit` | function | no | Callback on submit |
| `renderInput` | function | no | Custom input renderer (receives `{ value, onChange, onSubmit, onKeyDown }`) |

Can nest `<Autosuggest>` inside for autocomplete.

### `<Autosuggest>` — Autocomplete

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `fields` | string[] | yes | Fields to search for suggestions |
| `returnFields` | string[] | no | Fields to include in suggestion results |
| `limit` | number | no | Max suggestions (default: 10) |
| `minChars` | number | no | Min chars to trigger (default: 2) |
| `debounceMs` | number | no | Debounce delay (default: 300) |
| `semanticIndexes` | string[] | no | Vector indexes for semantic suggestions |
| `renderSuggestion` | function | no | Custom suggestion renderer |
| `onSuggestionSelect` | function | no | Callback on selection |
| `table` | string | no | Table override |
| `filterQuery` | object | no | Filter constraint |
| `layout` | string | no | `"vertical"` \| `"horizontal"` \| `"grid"` \| `"custom"` |

Composable: can nest `<AutosuggestResults>` and `<AutosuggestFacets>` inside for sectioned dropdowns.

### `<Facet>` — Faceted Navigation

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `id` | string | yes | Unique ID |
| `fields` | string[] | yes | Facet fields (**must be `keyword` type**) |
| `initialValue` | string[] | no | Pre-selected values |
| `itemsPerBlock` | number | no | Items per page |
| `placeholder` | string | no | Search input placeholder |
| `showFilter` | boolean | no | Show search input (default: true) |
| `seeMore` | string | no | "Show more" button text |
| `table` | string | no | Table override |
| `items` | function | no | Custom render: `(data, { handleChange, isChecked }) => ReactNode` |

### `<Results>` — Search Results

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `id` | string | yes | Unique ID |
| `searchBoxId` | string | no | ID of QueryBox that drives this (must match) |
| `fields` | string[] | no | Fields to search |
| `semanticIndexes` | string[] | no | Vector indexes (**required for semantic search**) |
| `limit` | number | no | For semantic search limit |
| `itemsPerPage` | number | no | Results per page (default: 10) |
| `initialPage` | number | no | Starting page |
| `items` | function | yes | Render function: `(hits: QueryHit[]) => ReactNode` |
| `pagination` | function | no | Custom pagination: `(total, perPage, page, setPage) => ReactNode` |
| `stats` | function | no | Stats display: `(total) => ReactNode` |
| `sort` | object | no | Sort config: `{ field, order }` |
| `customQuery` | function | no | Custom query builder |
| `table` | string | no | Table override |
| `filterQuery` | object | no | Additional filter |
| `exclusionQuery` | object | no | Exclusion filter |

### `<ActiveFilters>` — Active Filter Display

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `id` | string | yes | Unique ID |
| `render` | function | yes | `(filters, removeFilter) => ReactNode` |

### `<RAGResults>` — RAG Answer with Sources

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `id` | string | yes | Unique ID |
| `searchBoxId` | string | yes | ID of QueryBox (must use `mode="submit"`) |
| `summarizer` | object | yes | `{ provider, model, api_key? }` |
| `systemPrompt` | string | no | Custom LLM instructions |
| `fields` | string[] | no | Fields to search |
| `semanticIndexes` | string[] | no | Vector indexes |
| `showHits` | boolean | no | Show source documents (default: false) |
| `renderSummary` | function | no | `(summary, isStreaming, hits) => ReactNode` |
| `table` | string | no | Table override |
| `filterQuery` | object | no | Additional filter |
| `children` | ReactNode | no | Nest `<AnswerFeedback>` inside |

Use with `replaceCitations(text, fn)` from `@antfly/components` to render citation links.

### `<AnswerResults>` — Answer Agent Q&A

Full-featured answer agent with reasoning, follow-ups, and confidence.

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `id` | string | yes | Unique ID |
| `searchBoxId` | string | yes | ID of QueryBox |
| `generator` | object | yes | `{ provider, model, api_key? }` |
| `systemPrompt` | string | no | Custom LLM instructions |
| `fields` | string[] | no | Fields to search |
| `semanticIndexes` | string[] | no | Vector indexes |
| `showReasoning` | boolean | no | Show agent reasoning |
| `showFollowUpQuestions` | boolean | no | Show suggested follow-ups |
| `showClassification` | boolean | no | Show query classification |
| `showConfidence` | boolean | no | Show answer confidence |
| `showHits` | boolean | no | Show source documents |
| `renderAnswer` | function | no | `(answer, isStreaming, hits) => ReactNode` |
| `renderFollowUpQuestions` | function | no | `(questions) => ReactNode` |
| `renderReasoning` | function | no | `(reasoning) => ReactNode` |
| `onStreamStart` | function | no | Callback when streaming begins |
| `onStreamEnd` | function | no | Callback when streaming ends |
| `onError` | function | no | Error callback |
| `agentKnowledge` | string | no | Additional context for the agent |
| `eval` | object | no | Evaluation config |
| `children` | ReactNode | no | Nest `<AnswerFeedback>` inside |

### `<AnswerFeedback>` — User Ratings

Nest inside `<RAGResults>` or `<AnswerResults>`.

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `scale` | number | yes | 1 = thumbs, 4 = stars, any = numeric |
| `renderRating` | function | yes | Use built-in: `renderThumbsUpDown`, `renderStars`, `renderNumeric` |
| `onFeedback` | function | yes | `({ feedback, result, query }) => void` |

## Generator/Summarizer Providers

Used in `<RAGResults>` (summarizer) and `<AnswerResults>` (generator):

| Provider | Value | Example models |
|----------|-------|---------------|
| Ollama | `"ollama"` | gemma3:4b, qwen2.5:7b |
| OpenAI | `"openai"` | gpt-4o, gpt-4o-mini |
| Anthropic | `"anthropic"` | claude-sonnet-4-20250514 |
| AWS Bedrock | `"bedrock"` | anthropic.claude-v2 |
| Google | `"google"` | gemini-2.0-flash |

## Sharp Edges

1. **Must import CSS**: `import '@antfly/components/dist/components.css'` — components render unstyled without it
2. **`searchBoxId` must match** the `id` on the QueryBox that drives the Results/RAGResults/AnswerResults
3. **`semanticIndexes` required** for vector search — same rule as the API
4. **`mode="submit"`** for Q&A: RAGResults and AnswerResults need submit mode on QueryBox, not live mode
5. **Facet fields must be `keyword` type** — `text` fields produce broken facet values
6. **Provider config differs**: `summarizer` for RAGResults, `generator` for AnswerResults — different prop names, same shape
7. **URL state sync**: Antfly provider syncs search state to URL query params via `onChange` — be aware this affects browser history
8. **Peer dependencies**: `@antfly/sdk`, `react`, `react-dom` must be installed separately
