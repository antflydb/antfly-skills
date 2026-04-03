# Frontend Patterns — UI Recipes

## Search Page with Facets

**Goal**: Classic search experience — type, filter, browse results.

**Pattern**:
1. `<Antfly url={...} table={...} headers={...}>`
2. `<QueryBox id="search" mode="live">` with `<Autosuggest>` for autocomplete
3. Sidebar: multiple `<Facet>` components on keyword fields (category, brand, price range)
4. `<ActiveFilters>` to show/remove selected facets
5. `<Results searchBoxId="search" fields={["title","desc"]} items={renderCards}>` with custom card renderer
6. Add `semanticIndexes={["emb"]}` to Results for hybrid search (keyword + semantic)

**Key decisions**:
- `mode="live"` for instant search, `mode="submit"` if you want explicit search button
- Facets need `keyword` typed fields in the schema
- `itemsPerPage` on Results controls pagination chunk size

## Q&A / Chat Interface

**Goal**: User asks a question, gets a streaming LLM-generated answer with source citations.

**Pattern**:
1. `<Antfly url={...} table={...}>`
2. `<QueryBox id="q" mode="submit" placeholder="Ask a question..." buttonLabel="Ask">`
3. `<AnswerResults id="answer" searchBoxId="q" generator={{ provider: "openai", model: "gpt-4o" }} semanticIndexes={["emb"]} showReasoning={true} showFollowUpQuestions={true}>`
4. Nest `<AnswerFeedback scale={1} renderRating={renderThumbsUpDown} onFeedback={handler}>` inside
5. Custom `renderAnswer` to format markdown with citations using `replaceCitations`

**Key decisions**:
- Always `mode="submit"` — you don't want to fire the agent on every keystroke
- Choose generator provider based on quality/cost tradeoff
- `showHits={true}` to display source documents alongside the answer
- Follow-up questions can be wired back to the QueryBox for conversational flow

## Custom Search Input

**Goal**: Replace the default QueryBox input with your own design system component.

**Pattern**:
```
<QueryBox id="search" mode="live"
  renderInput={({ value, onChange, onSubmit, onKeyDown }) => (
    <YourCustomInput value={value} onChange={onChange} onKeyDown={onKeyDown} />
  )}
>
  <Autosuggest fields={["title"]} />
</QueryBox>
```

The render prop receives: `value`, `onChange`, `onSubmit`, `onKeyDown`, `isSuggestOpen`, `onSuggestClose`, `placeholder`, `disabled`, `id`.

## Fully Custom UI with Hooks

**Goal**: Build a completely custom interface without using the component library's UI.

**Pattern**:
1. Use `@antfly/sdk` directly for queries: `client.query(...)`, `client.agents.retrieval(...)`
2. Use `useAnswerStream` hook for streaming RAG without `<AnswerResults>`
3. Use `useCitations` to parse citations from streamed answers
4. Use `useSearchHistory` for recent searches

This approach gives full control over rendering while still leveraging Antfly's streaming and citation parsing.

## Rendering Streamed Markdown

Answers from RAG/AnswerResults arrive as streaming markdown. For smooth rendering:

1. Use a streaming-capable markdown renderer (e.g., `streamdown`, `react-markdown`)
2. Process citations with `replaceCitations(answer, mapFn)` before rendering
3. Handle `isStreaming` state to show a loading indicator

Example with `renderAnswer`:
```
renderAnswer={(answer, isStreaming, hits) => (
  <div>
    <Streamdown markdown={replaceCitations(answer, (id) => `[${hitIndex(id)}]`)} />
    {isStreaming && <Spinner />}
  </div>
)}
```

## Sharp Edges

- `<Antfly>` provider syncs state to URL params — if you have your own routing, use `onChange` to manage conflicts
- Multiple QueryBoxes on one page: each needs a unique `id`, and Results components specify which one they listen to via `searchBoxId`
- `<Autosuggest>` debounces by default (300ms) — set `debounceMs={0}` for instant suggestions (higher load)
- Component state resets on `table` prop change — switching tables clears results and filters
