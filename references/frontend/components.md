# React Components — `@antfly/components`

## Installation

```
npm install @antfly/components@^0.3.0 @antfly/sdk@^0.3.0 react react-dom
```

`@antfly/components` 0.3.0 peer-requires `@antfly/sdk` `^0.3.0` — an older SDK does not satisfy it.

Import stylesheet (required): `import '@antfly/components/styles'`

Entry points: `@antfly/components` (everything) and `@antfly/components/adapters` (AI Elements render-prop adapters).

## Component Reference

### `<Antfly>` — Root Provider

**Required.** All other components must be descendants — except `<Pagination>` and `<ResearchReport>`, which read no context and work standalone.

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `url` | string | yes | Antfly base URL. A trailing `/db/v1`, `/auth/v1`, or `/ai/v1` is stripped, so either form works |
| `table` | string | yes | Default table for all child components |
| `headers` | object | no | Custom headers (auth, etc.) |
| `onChange` | `(params: Map<string, unknown>) => void` | no | Fires on mount and then only when the serialized widget values or pages change — not on every render. The map carries each widget's value plus a `<id>Page` entry for every widget past page 1 |
| `children` | ReactNode | yes | |

### `<QueryBox>` — Search Input

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `id` | string | yes | Unique ID (referenced by Results/AnswerResults via `searchBoxId`) |
| `mode` | `"live"` \| `"submit"` | no | `live` (default) = search as you type; `submit` = on enter/button |
| `placeholder` | string | no | Defaults to `"search…"` in live mode, `"Ask a question..."` in submit mode |
| `buttonLabel` | string | no | Submit button text (default `"Submit"`, submit mode only) |
| `initialValue` | string | no | Pre-filled value; re-applied whenever the prop changes |
| `autoSubmit` | boolean | no | Submit `initialValue` on mount (submit mode only, default false) |
| `submitSignal` | string \| number | no | Change it to re-fire an `autoSubmit` for the same `initialValue` |
| `clearOnSubmit` | boolean | no | Clear the input after submit (default false) |
| `onInputChange` | `(value: string) => void` | no | Every keystroke |
| `onSubmit` | `(value: string) => void` | no | On submit |
| `onEscape` | `(clearInput: () => void) => boolean` | no | Return `true` to suppress the built-in Escape handling |
| `renderInput` | `(props: CustomInputProps) => ReactNode` | no | Replace the default `<input>` |
| `children` | ReactNode | no | Nest `<Autosuggest>` for autocomplete |

`CustomInputProps` supplied to `renderInput`: `value`, `onChange(value)`, `onSubmit(value)`, `onKeyDown(event)`, `isSuggestOpen`, `onSuggestClose()`, `placeholder`, `id` (`"{id}-input"`). The interface also declares `disabled?`, but QueryBox never sets it.

### `<Autosuggest>` — Autocomplete

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `fields` | string[] | no | Fields to search for suggestions |
| `returnFields` | string[] | no | Fields to return (defaults to `fields`) |
| `limit` | number | no | Max suggestions (default 10) |
| `minChars` | number | no | Min chars to trigger (default 2) |
| `debounceMs` | number | no | Debounce delay (default 300, `0` disables) |
| `semanticIndexes` | string[] | no | Vector indexes for semantic suggestions |
| `customQuery` | `(value?, fields?) => unknown` | no | Replace the generated query |
| `renderSuggestion` | `(hit: QueryHit) => ReactNode` | no | Custom suggestion renderer |
| `onSuggestionSelect` | `(hit: QueryHit) => void` | no | Overrides QueryBox's default "fill the input" behaviour |
| `table` | string | no | Table override |
| `filterQuery` / `exclusionQuery` | object | no | Constrain suggestions |
| `layout` | `"vertical"` \| `"horizontal"` \| `"grid"` \| `"custom"` | no | Default `"vertical"` |
| `className` / `dropdownClassName` | string | no | |
| `children` | ReactNode | no | `<AutosuggestResults>` / `<AutosuggestFacets>` for sectioned dropdowns |

`searchValue`, `isOpen`, `containerRef`, and `onClose` are injected by QueryBox onto any non-DOM child — do not set them. QueryBox also injects its default `onSuggestionSelect` ("fill the input") whenever the child supplies none of its own.

### `<AutosuggestResults>` — Suggestion Section

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `limit` | number | no | Cap items shown in this section |
| `renderItem` | `(hit, index) => ReactNode` | no | |
| `onSelect` | `(hit: QueryHit) => void` | no | |
| `filter` | `(hit) => boolean` | no | |
| `header` | ReactNode \| `(count) => ReactNode` | no | |
| `footer` / `emptyMessage` | ReactNode | no | |
| `className` / `itemClassName` / `selectedItemClassName` | string | no | |

### `<AutosuggestFacets>` — Facet Section In The Dropdown

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `field` | string | yes | Single facet field (keyword type) |
| `size` | number | no | Terms to request (default 5) |
| `label` | string | no | Section label |
| `order` | `"count"` \| `"term"` \| `"reverse_count"` \| `"reverse_term"` | no | |
| `renderItem` | `(facet, index) => ReactNode` | no | |
| `renderSection` | `(field, label, terms) => ReactNode` | no | |
| `onSelect` | `(facet: AggregationBucket) => void` | no | |
| `clickable` | boolean | no | |
| `filter` | `(facet) => boolean` | no | |
| `header` | ReactNode \| `(field, label) => ReactNode` | no | |
| `footer` / `emptyMessage` | ReactNode | no | |
| `className` / `itemClassName` / `sectionClassName` | string | no | |

### `<Facet>` — Faceted Navigation

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `id` | string | yes | Unique ID |
| `fields` | string[] | yes | Facet fields (**must be `keyword` type**) |
| `initialValue` | string[] | no | Pre-selected values |
| `itemsPerBlock` | number | no | Items per block (default 5, also the "see more" increment) |
| `placeholder` | string | no | Filter input placeholder (default `"filter…"`) |
| `showFilter` | boolean | no | Show the filter input (default true) |
| `filterValueModifier` | `(value: string) => string` | no | Transforms the typed filter value into a pattern: a bucket matches when `new RegExp(modifier(value), "i")` tests its key; an invalid pattern matches nothing. Without it, filtering is case-insensitive substring matching. Filtering is client-side, inside `Facet` (`facetFilterMatches`) |
| `seeMore` | string | no | "See more" button text |
| `table` | string | no | Table override |
| `items` | `(data, { handleChange, isChecked }) => ReactNode` | no | Custom render |

### `<Results>` — Search Results

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `id` | string | yes | Unique ID |
| `searchBoxId` | string | no | ID of the QueryBox that drives this |
| `fields` | string[] | no | Always forwarded as the query's result-field projection, including in semantic mode. In full-text mode it also picks the fields the generated query matches on |
| `customQuery` | `(query?: string) => unknown` | no | Replaces the generated full-text query. Called with the search value in full-text mode; in semantic mode it is called with **no arguments** and its return is sent as `full_text_search` alongside the semantic query |
| `semanticIndexes` | string[] | no | Vector indexes (**required for semantic search**) |
| `limit` | number | no | Does **not** size this widget's query. It only sets the `semantic_search` limit of sibling `Facet` queries (default 10) |
| `itemsPerPage` | number | no | Page size (default 10) — sizes the query in **both** modes: `limit: itemsPerPage`, `offset: (page - 1) * itemsPerPage` |
| `initialPage` | number | no | Starting page (default 1) |
| `items` | `(hits: QueryHit[]) => ReactNode` | yes | Render function |
| `pagination` | `(total, itemsPerPage, page, setPage) => ReactNode` | no | Custom pagination |
| `stats` | `(total: number) => ReactNode` | no | Replaces the default count line |
| `onResults` | `(hits: QueryHit[], total: number) => void` | no | Fires once per new result set |
| `sort` | unknown | no | Forwarded verbatim as the query's `order_by`, i.e. `[{ field, desc? }]` |
| `table` | string | no | Table override |
| `filterQuery` / `exclusionQuery` | object | no | Extra constraints |

### `<Pagination>` — Standalone Pager

Rendered automatically by `Results` for full-text queries; export it to build your own.

| Prop | Type | Required |
|------|------|----------|
| `page` | number | yes |
| `total` | number | yes |
| `itemsPerPage` | number | yes |
| `onChange` | `(page: number) => void` | yes |

Caps out at `10000 / itemsPerPage` pages.

### `<ActiveFilters>` — Active Filter Display

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `items` | `(filters: ActiveFilter[], removeFilter: (id: string) => void) => ReactNode` | no | Custom render |

`ActiveFilter` is `{ key, value }` where `key` is the widget id.

### `<AnswerResults>` — Answer Agent Q&A

Single-shot streaming answer with reasoning, follow-ups, confidence, citations, and optional eval output. Fires when its QueryBox is *submitted*.

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `id` | string | yes | Unique ID |
| `searchBoxId` | string | yes | ID of the driving QueryBox |
| `generator` | `GeneratorConfig` | yes | `{ provider, model, ... }` — required since 0.3.0 |
| `table` | string | no | Overrides the QueryBox/provider table |
| `fields` | string[] | no | Fields to return |
| `semanticIndexes` | string[] | no | Vector indexes |
| `filterQuery` / `exclusionQuery` | object | no | Mandatory table predicates for retrieval |
| `agentKnowledge` | string | no | Domain knowledge injected into the agent's system prompt |
| `systemPrompt` | string | no | → `steps.generation.system_prompt` |
| `generationContext` | string | no | → `steps.generation.generation_context` |
| `limit` | number | no | Retrieval limit (default 10) |
| `followUpCount` | number | no | → `steps.followup.count` |
| `eval` | `EvalConfig` | no | Inline answer evaluation |
| `showFollowUpQuestions` | boolean | no | Default **true**. `steps.followup` is only sent when on, so turning it off stops the server producing them: `onFollowup` never fires and `renderFollowUpQuestions` is dead |
| `showReasoning` | boolean | no | Default false. Sends `steps.classification` with `with_reasoning: true` |
| `showClassification` | boolean | no | Default false. `steps.classification` is only sent when this or `showReasoning` is on |
| `showConfidence` | boolean | no | Default false. `steps.confidence` is only sent when on, so leaving it off means `onConfidence` never fires and `renderConfidence` is dead |
| `showHits` | boolean | no | Default false |
| `renderLoading` | `() => ReactNode` | no | |
| `renderEmpty` | `() => ReactNode` | no | |
| `renderAnswer` | `(answer, isStreaming, hits?) => ReactNode` | no | |
| `renderReasoning` | `(reasoning, isStreaming) => ReactNode` | no | |
| `renderClassification` | `(data) => ReactNode` | no | |
| `renderFollowUpQuestions` | `(questions: string[]) => ReactNode` | no | |
| `renderConfidence` | `(confidence) => ReactNode` | no | |
| `renderHits` | `(hits: QueryHit[]) => ReactNode` | no | |
| `renderEvalResult` | `(evalResult) => ReactNode` | no | |
| `onController` | `(controller: AbortController) => void` | no | Receives each request's controller before the request starts (including the header wait) — call `abort()` to cancel |
| `onRequestContextChange` | `() => void` | no | Fires when request settings change (url, headers, table, generator, fields, indexes, filters, prompts, limits, `show*` flags …). The in-flight stream is aborted and all answer state is cleared. Incidental re-renders and explicit aborts do not trigger it |
| `onStreamStart` / `onStreamEnd` | `() => void` | no | |
| `onError` | `(error: string) => void` | no | Receives a string, not an `Error` |
| `onClassification` | `(data) => void` | no | |
| `onHit` | `(hit: QueryHit) => void` | no | |
| `onGenerationChunk` | `(chunk: string) => void` | no | |
| `onConfidence` | `(data) => void` | no | |
| `onFollowup` | `(question: string) => void` | no | |
| `children` | ReactNode | no | Nest `<AnswerFeedback>` |

Children can read everything via `useAnswerResultsContext()`. Render citation links with `replaceCitations` / `useCitations` (see `hooks.md`).

### `<AnswerFeedback>` — User Ratings

Nest inside `<AnswerResults>`. Throws if used elsewhere. Hidden while streaming and until an answer exists.

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `scale` | number | yes | Rating range is `0..scale` (1 = thumbs, 4 = 5 stars) |
| `renderRating` | `(currentRating: number \| null, onRate: (n: number) => void) => ReactNode` | no | Nothing renders without it |
| `renderComment` | `(comment: string, setComment: (v: string) => void) => ReactNode` | no | The comment field only appears when this is supplied |
| `renderSubmit` | `(onSubmit: () => void) => ReactNode` | no | Defaults to a "Submit Feedback" button |
| `renderSubmitted` | `() => ReactNode` | no | Defaults to a thank-you heading |
| `onFeedback` | function | yes | `({ feedback, result, query, context? }) => void` |

`feedback` is `{ rating, scale, comment? }`; `result` is the `RetrievalAgentResult`; `context` carries `{ classification?, reasoning?, agentKnowledge? }`.

Built-in renderers: `renderThumbsUpDown`, `renderStars`, `renderNumeric`. The first two match `renderRating` directly; `renderNumeric` takes a third `scale` argument, so wrap it: `renderRating={(r, onRate) => renderNumeric(r, onRate, 4)}`.

### `<ChatBar>` — Multi-Turn Chat

Self-contained conversation UI: renders `<ChatMessages>` and `<ChatInput>` internally and provides `ChatContext`. Accepts every `ChatMessagesProps` and `ChatInputProps` field plus:

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `id` | string | yes | Unique ID |
| `generator` | `GeneratorConfig` | yes | Required since 0.3.0 |
| `table` | string | no | Table override |
| `semanticIndexes` | string[] | no | |
| `fields` | string[] | no | |
| `filterQuery` / `exclusionQuery` | object | no | |
| `agentKnowledge` / `systemPrompt` | string | no | |
| `limit` | number | no | Results per search |
| `maxInternalIterations` | number | no | `1+` = agentic tool-calling. For pipeline mode omit it or pass `0` — `0` is falsy, so the field is dropped from the request and the API's own default of `0` applies |
| `followUpCount` | number | no | |
| `steps` | `RetrievalAgentSteps` | no | **Replaces** the default steps (`generation`, `classification`, `followup`, `confidence`) instead of merging into them, so `followUpCount` is dropped. `systemPrompt` is still merged into `steps.generation` — but only if your `steps` includes a `generation` entry |
| `tools` | `ChatToolsConfig` | no | Agentic-mode tool config, sent as the request's top-level `tools` whether or not `steps` is supplied |
| `onStreamStart` / `onStreamEnd` | `() => void` | no | |
| `onError` | `(error: string) => void` | no | |
| `children` | ReactNode | no | Rendered after the input |

`ChatMessagesProps`: `showHits`, `showFollowUpQuestions`, `showConfidence`, `renderUserMessage(message, turn)`, `renderAssistantMessage(message, isStreaming, turn)`, `renderHits(hits, turn)`, `renderFollowUpQuestions(questions, onSelect, turn)`, `renderClarification(clarification, onRespond, turn)`, `renderConfidence(confidence, turn)`, `renderStreamingIndicator()`, `renderError(error, turn)`.

`ChatInputProps`: `placeholder`, `renderInput({ value, onChange, onSubmit, isStreaming, placeholder, abort })`.

`<ChatMessages>` and `<ChatInput>` are also exported individually for custom layouts, but they require a `ChatContext` — i.e. they must live inside a `<ChatBar>`.

### `<ResearchReport>` — Research Agent Report

Renders a Research Agent report: title, executive summary, sections, and a numbered sources list, with `[E#]` citation markers resolved against the evidence registry. Takes a final `ResearchAgentResult` or any `{ report?, evidence? }` (`ResearchReportResult`) — e.g. one assembled from `useResearchStream`. Reads no context.

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `result` | `ResearchReportResult` | yes | `{ report?: ResearchReport, evidence?: ResearchEvidence[] }` |
| `renderCitation` | `(evidence: ResearchEvidence \| undefined, marker: string) => ReactNode` | no | Default: superscript link to `#evidence-<id>`; `evidence` is `undefined` for an unresolved marker |
| `showSummary` | boolean | no | Default true |
| `showSources` | boolean | no | Default true |
| `renderEmpty` | `() => ReactNode` | no | Shown while the report has neither sections nor markdown |
| `className` | string | no | |

Section markdown is split into paragraphs on blank lines and rendered as plain text, not parsed as markdown. `evidenceLabel(evidence)` gives the label it uses: `title`, else `url`, else `table/doc_id`, else `table`, else `id`.

### `<CustomWidget>` — Context Escape Hatch

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `children` | ReactNode | yes | Each element child is cloned with `ctx` (`SharedState`) and `dispatch` props |

### `<Listener>` — Query Orchestrator

Rendered by `<Antfly>` automatically; it batches every widget's query into one multiquery and writes results back. Exported for advanced trees only. Props: `children`, `onChange`.

### AI Elements Adapters

`createAIElementsRenderers(components, options?)` returns ChatBar render props backed by AI Elements components (`Message`, `Sources`, `Suggestions`, `PromptInput`, …). Companions: `hitToSourceProps`, `turnToStatus`, `confidenceLabel`. Available from `@antfly/components` or `@antfly/components/adapters`.

## Generator Providers

`generator={{ provider, model }}` is required on `AnswerResults` / `ChatBar`. `GeneratorProvider` (SDK 0.3.0, matching the SDK's `generatorProviders` array) is one of `cloudflare`, `anthropic`, `antfly`, `bedrock`, `apple`, `gemini`, `ollama`, `openai`, `chatgpt`, `openrouter`, `vertex`. `cohere` and `mock` are no longer accepted by the type. The request goes to `/db/v1/agents/retrieval`; which providers the server runs (and which can drive the agentic tool loop) is covered in `../backend/rag.md`.

## Sharp Edges

1. **Must import CSS**: `import '@antfly/components/styles'` — components render unstyled without it
2. **`searchBoxId` must match** the driving QueryBox `id`. A mismatch throws nothing. In full-text mode `Results` sees an empty search value and matches everything; in semantic mode an empty or mismatched value leaves the widget contributing neither a full-text nor a semantic query, so the `Listener`'s readiness check never passes and the entire batched request is skipped — sibling `Facet`s get no data either. `AnswerResults` never fires
3. **`semanticIndexes` required** for vector search — same rule as the API
4. **`generator` is required** on `AnswerResults` and `ChatBar` (and `ChatConfig` for `useChatStream`) — omitting it is a type error since 0.3.0
5. **`AnswerResults` needs a submission.** In `mode="live"` typing never sets `submittedAt`, so nothing fires; the one exception is picking an Autosuggest entry with the default select handler, which does submit in live mode. Use `mode="submit"` for Q&A
6. **`Results` hides pagination when semantic search is on** — which needs **both** `semanticIndexes` and `searchBoxId`. With `semanticIndexes` but no `searchBoxId` the widget stays in full-text mode: the pager renders and the query carries no `semantic_search`. When semantic mode is on, only the pager UI is suppressed — the query is still one `itemsPerPage`-sized page (`limit: itemsPerPage`, `offset: (page - 1) * itemsPerPage`), exactly as in full-text mode; `Results.limit` never sizes it
7. **`Results.sort` is passed straight through** to `order_by`; give it the API shape `[{ field: "price", desc: true }]`, not a bare string
8. **Facet fields must be `keyword` type** — `text` fields produce broken facet values
9. **`ActiveFilters` uses `items`**, not `render`, for custom rendering
10. **`renderInput` on QueryBox disables the form wrapper**, the clear button, and the submit button — your component owns submission. Either call the supplied `onSubmit`, or forward the supplied `onKeyDown`, which already submits on Enter in submit mode
11. **`AnswerFeedback` renders an empty container without `renderRating`** — there is no default rating UI, and with the rating stuck at `null` the submit button never appears either. The comment box only appears when `renderComment` is given
12. **Peer dependencies**: `@antfly/sdk` `^0.3.0`, `react` (16–19), and `react-dom` must be installed separately
