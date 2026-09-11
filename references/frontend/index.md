# Antfly — Frontend Skill

## What Exists

Antfly provides two frontend packages (both published at `0.0.14`):

- **`@antfly/sdk`** (npm) — TypeScript client for the Antfly REST API. Tables, queries, indexes, users, retrieval/chat agents, inference.
- **`@antfly/components`** (npm) — React component library that wires directly to an Antfly backend. Search UIs, answer-agent Q&A, multi-turn chat, facets, autocomplete, citations, and feedback components.

These are separate packages. `@antfly/components` depends on `@antfly/sdk`, `react`, and `react-dom` as peer dependencies.

## When To Read Which Frontend Module

- Need client setup, typed requests, or direct SDK usage:
  Read `sdk.md`
- Need React component props or wiring rules:
  Read `components.md`
- Need custom streaming, citations, or search history:
  Read `hooks.md`
- Need app-level recipes:
  Read `patterns.md`

## UI Selection Guide

- Search page with facets and result cards:
  Use `Antfly` + `QueryBox` + `Facet` + `ActiveFilters` + `Results`
- One-shot streaming answer with citations and follow-ups:
  Use `QueryBox mode="submit"` + `AnswerResults`
- Multi-turn conversation with history:
  Use `ChatBar` (renders `ChatMessages` + `ChatInput` itself)
- Fully custom UI:
  Use `@antfly/sdk` and `useAnswerStream` / `useChatStream`

## How Components Connect

```tsx
<Antfly url="..." table="..." headers={...}>      {/* Provider: API URL, table, auth */}
  <QueryBox id="search">                          {/* Input: captures search text */}
    <Autosuggest fields={["title"]} />            {/* Dropdown: autocomplete */}
  </QueryBox>
  <Facet id="cat" fields={["category.keyword"]} /> {/* Sidebar: faceted filtering */}
  {/* Output: renders search hits */}
  <Results
    id="results" searchBoxId="search"
    fields={["title"]} semanticIndexes={["emb"]}
    items={(hits) => hits.map((h) => <Card key={h._id} {...h} />)}
  />
</Antfly>
```

Everything inside `<Antfly>` shares a reducer-backed context. QueryBox writes the input value, Facet contributes filter queries, and an internal `Listener` batches every widget's query into one multiquery request. Only the query widgets (`QueryBox`, `Facet`, `Results`, `Autosuggest`) go through the `Listener`; `AnswerResults` and `ChatBar` bypass it and call `streamAnswer` against the agent endpoint themselves.

## Skill Modules

- [sdk.md](sdk.md) — TypeScript SDK: client init, auth, queries, agents, streaming, types
- [components.md](components.md) — React components: every component, its props, how they wire together
- [hooks.md](hooks.md) — React hooks and contexts: useAnswerStream, useChatStream, useSearchHistory, useCitations
- [patterns.md](patterns.md) — UI recipes: search page, Q&A, chat, faceted catalog, custom input

## Critical Sharp Edges

1. `<Antfly>` provider is **required** — the query widgets (`QueryBox`, `Facet`, `Results`, `Autosuggest`, `ActiveFilters`, `CustomWidget`) plus `AnswerResults` and `ChatBar` call `useSharedContext()`, which throws `"useSharedContext must be used within a SharedContextProvider"` outside the provider. The rest answer to a different parent: `Pagination` reads no context at all, `AnswerFeedback` must sit inside `<AnswerResults>`, `ChatInput` / `ChatMessages` inside `<ChatBar>`, and `AutosuggestResults` / `AutosuggestFacets` inside `<Autosuggest>`
2. `semanticIndexes` must be passed to `<Results>` for vector search — same rule as the API. `<AnswerResults>` always sends `semantic_search`; there the prop only picks which indexes the retrieval query uses
3. `@antfly/components` requires `react` 16–19, `react-dom`, and `@antfly/sdk` as peer dependencies
4. Import the stylesheet: `import '@antfly/components/styles'` — without it components render unstyled
5. `QueryBox` defaults to `mode="live"` (searches as you type). `AnswerResults` and `ChatBar` only react to *submissions*, so pair `AnswerResults` with `mode="submit"`
6. `searchBoxId` on Results/AnswerResults must match the `id` on the QueryBox that drives it — a mismatch is not an error, it fails silently. In full-text mode `Results` falls back to matching everything; in semantic mode the empty search value leaves the widget contributing neither query, the `Listener`'s readiness check never passes, and the whole batched request is skipped — so sibling `Facet`s get no data either. `AnswerResults` never fires
7. Facet fields must be `keyword` type in the schema — `text` fields produce meaningless facet values
8. The provider does not sync URL state, but `fromUrlQueryString` / `toUrlQueryString` are exported for wiring it up through `onChange`
