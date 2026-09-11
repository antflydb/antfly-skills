# Frontend Patterns — UI Recipes

## Search Page with Facets

**Goal**: Classic search experience — type, filter, browse results.

**Pattern**:
1. `<Antfly url={...} table={...} headers={...}>`
2. `<QueryBox id="search">` (live is the default) with `<Autosuggest>` for autocomplete
3. Sidebar: multiple `<Facet>` components on keyword fields (category, brand, …)
4. `<ActiveFilters>` to show/remove selected facets
5. `<Results id="results" searchBoxId="search" fields={["title","desc"]} items={renderCards}>` with a custom card renderer (`id` is required)
6. Add `semanticIndexes={["emb"]}` to Results for semantic retrieval

**Key decisions**:
- `mode="live"` for instant search, `mode="submit"` for an explicit search button
- Facets need `keyword` typed fields in the schema
- `itemsPerPage` sizes the query in both modes (`limit`/`offset`); with `semanticIndexes` set Results still fetches one `itemsPerPage`-sized page but renders no pager. `Results.limit` does not size results — it only sets the `semantic_search` limit of sibling `Facet` queries
- `sort` is forwarded verbatim as `order_by`: `sort={[{ field: "price", desc: true }]}`

## Q&A with a Streaming Answer

**Goal**: User asks a question, gets a streaming LLM answer with source citations.

**Pattern**:
1. `<Antfly url={...} table={...}>`
2. `<QueryBox id="q" mode="submit" placeholder="Ask a question..." buttonLabel="Ask">`
3. `<AnswerResults id="answer" searchBoxId="q" generator={{ provider: "openai", model: "gpt-4o" }} semanticIndexes={["emb"]} showReasoning showHits>`
4. Nest `<AnswerFeedback scale={1} renderRating={renderThumbsUpDown} onFeedback={handler} />` inside
5. Custom `renderAnswer` to format markdown with citations using `replaceCitations`

**Key decisions**:
- `mode="submit"` is mandatory in practice — `AnswerResults` only reacts to submissions, and typing in a live-mode box never makes one. The single live-mode path that does submit is picking an Autosuggest entry with QueryBox's default select handler
- `showFollowUpQuestions` is on by default; `showReasoning`, `showClassification`, `showConfidence`, `showHits` are off
- Tune retrieval with `limit` (default 10), `filterQuery`, `exclusionQuery`, and `agentKnowledge`
- Wire follow-up questions back into the QueryBox via `initialValue` + `autoSubmit` + a changing `submitSignal`

## Multi-Turn Chat

**Goal**: A conversation with history, tool use, and clarification questions.

**Pattern**:
```tsx
<Antfly url={API} table="docs" headers={headers}>
  <ChatBar
    id="chat"
    generator={{ provider: "anthropic", model: "claude-sonnet-4-20250514" }}
    semanticIndexes={["emb"]}
    maxInternalIterations={5}     // 1+ = agentic; omit or pass 0 (dropped from the request) for pipeline mode
    showHits
    renderAssistantMessage={(message, isStreaming) => (
      <Streamdown>{replaceCitations(message, { renderCitation: renderAsSequentialLinks })}</Streamdown>
    )}
  />
</Antfly>
```

`ChatBar` renders its own messages list and input, and pulls `url`, `headers`, and the default table from the provider. For a bespoke layout, drive `useChatStream` directly (see `hooks.md`).

## Custom Search Input

**Goal**: Replace the default QueryBox input with your own design system component.

```tsx
<QueryBox
  id="search"
  mode="submit"
  renderInput={({ value, onChange, onSubmit, onKeyDown, placeholder, id }) => (
    <YourInput
      id={id}
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={onKeyDown}
      onSubmitClick={() => onSubmit(value)}
    />
  )}
>
  <Autosuggest fields={["title"]} />
</QueryBox>
```

The render prop receives `value`, `onChange(value)`, `onSubmit(value)`, `onKeyDown(event)`, `isSuggestOpen`, `onSuggestClose()`, `placeholder`, and `id`. `CustomInputProps` also declares `disabled?`, which QueryBox never sets.

## Fully Custom UI with Hooks

**Goal**: Build a completely custom interface without the component library's UI.

1. Use `@antfly/sdk` directly: `client.query(...)`, `client.retrievalAgent(...)`, `client.chatAgent(...)`
2. Use `useAnswerStream` for one-shot streaming, `useChatStream` for conversations
3. Use `useCitations` (or the standalone helpers) to render citations
4. Use `useSearchHistory` for recent searches

Both stream hooks are provider-independent: you supply `url` and `headers` yourself.

## Rendering Streamed Markdown

Answers arrive as streaming markdown. For smooth rendering:

1. Use a streaming-capable markdown renderer (e.g. `streamdown`, `react-markdown`)
2. Rewrite citations before rendering — `replaceCitations` takes an options **object**
3. Use `isStreaming` for a loading indicator

```tsx
import { renderAsSequentialLinks, replaceCitations } from '@antfly/components'

renderAnswer={(answer, isStreaming, hits) => (
  <div>
    <Streamdown>
      {replaceCitations(answer, { renderCitation: renderAsSequentialLinks })}
    </Streamdown>
    {isStreaming && <Spinner />}
  </div>
)}
```

`renderAsSequentialLinks(ids, allIds)` emits `[[1]](#hit-<id>)` markdown links numbered by first appearance; `renderAsMarkdownLinks(ids)` keeps the raw resource IDs. For anything else pass your own `(ids, allIds) => string`.

To show only cited sources, filter the hits:

```tsx
const citedIds = getCitedResourceIds(answer)
const citedHits = hits.filter((hit) => citedIds.includes(hit._id))
```

## URL State Sync

The provider does not read or write the URL, but the helpers exist:

```tsx
import { fromUrlQueryString, toUrlQueryString } from '@antfly/components'

<Antfly
  url={API}
  table="docs"
  onChange={(params) => {
    const qs = toUrlQueryString(params)          // Map<string, unknown> → query string
    window.history.replaceState(null, '', qs ? `?${qs}` : window.location.pathname)
  }}
>
```

`fromUrlQueryString(location.search)` gives back a `Map` you can read `initialValue` / `initialValue[]` props from on first render.

## Sharp Edges

- `<Antfly>` does not sync URL params on its own — wire `onChange` + `toUrlQueryString` / `fromUrlQueryString`
- Multiple QueryBoxes on one page: each needs a unique `id`, and every Results/AnswerResults names the one it listens to via `searchBoxId`. A wrong id fails silently
- `<Autosuggest>` debounces 300ms by default — `debounceMs={0}` for instant suggestions (higher load)
- Supplying `renderInput` removes QueryBox's `<form>` wrapper along with its clear and submit buttons; your component must either call `onSubmit` or forward `onKeyDown`, which submits on Enter in submit mode
- Changing the `table` prop on `<Antfly>` re-runs queries but does not clear facet selections or the input — reset that state yourself if you need a clean slate
