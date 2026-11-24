# Antfly — Frontend Skill

## What Exists

Antfly provides two frontend packages, both at `0.3.0` on npm:

- **`@antfly/sdk`** — TypeScript client for the Antfly REST API. Tables, queries, indexes, users, retrieval/chat/research agents, SQL, graphs, memory, time series, inference. Subpaths `@antfly/sdk/sources` and `@antfly/sdk/kysely`.
- **`@antfly/components`** — React component library that wires directly to an Antfly backend. Search UIs, answer-agent Q&A, multi-turn chat, research reports, facets, autocomplete, citations, and feedback components.

These are separate packages. `@antfly/components` 0.3.0 peer-requires `@antfly/sdk` `^0.3.0`, `react`, and `react-dom` — install matching versions.

Related packages on npm, not covered here:

- `@antfly/design-system` `0.3.0` — shared shadcn/ui component library, tokens, and theme CSS
- `@antfly/graph` `0.0.3` — `ForceGraph` and `GraphLegend` React components plus `@antfly/graph/styles.css`; peer-requires `@antfly/design-system` `0.0.6` exactly
- `@antfly/embedded` `0.3.2` — Node binding for local Antfly databases and inference (libantfly C ABI), `node >= 24`

The upstream source tree also contains `ai-sdk`, `langchain`, `langgraph-store`, `better-auth`, and `web` packages; none is published to npm.

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
- Long-running cited research report:
  Use `useResearchStream` + `ResearchReport`
- Fully custom UI:
  Use `@antfly/sdk` and `useAnswerStream` / `useChatStream` / `useResearchStream`

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
- [hooks.md](hooks.md) — React hooks and contexts: useAnswerStream, useChatStream, useResearchStream, useSearchHistory, useCitations
- [patterns.md](patterns.md) — UI recipes: search page, Q&A, chat, research report, custom input, URL sync

## Critical Sharp Edges

1. `<Antfly>` provider is **required** — the query widgets (`QueryBox`, `Facet`, `Results`, `Autosuggest`, `ActiveFilters`, `CustomWidget`) plus `AnswerResults` and `ChatBar` call `useSharedContext()`, which throws `"useSharedContext must be used within a SharedContextProvider"` outside the provider. The rest answer to a different parent: `Pagination` and `ResearchReport` read no context at all, `AnswerFeedback` must sit inside `<AnswerResults>`, `ChatInput` / `ChatMessages` inside `<ChatBar>`, and `AutosuggestResults` / `AutosuggestFacets` inside `<Autosuggest>`
2. `semanticIndexes` must be passed to `<Results>` for vector search — same rule as the API. `<AnswerResults>` always sends `semantic_search`; there the prop only picks which indexes the retrieval query uses
3. `@antfly/components` 0.3.0 requires `react` 16–19, `react-dom`, and `@antfly/sdk` `^0.3.0` as peer dependencies. `generator` is required on `AnswerResults` and `ChatBar`
4. Import the stylesheet: `import '@antfly/components/styles'` — without it components render unstyled
5. `QueryBox` defaults to `mode="live"` (searches as you type). `AnswerResults` and `ChatBar` only react to *submissions*, so pair `AnswerResults` with `mode="submit"`
6. `searchBoxId` on Results/AnswerResults must match the `id` on the QueryBox that drives it — a mismatch is not an error, it fails silently. In full-text mode `Results` falls back to matching everything; in semantic mode the empty search value leaves the widget contributing neither query, the `Listener`'s readiness check never passes, and the whole batched request is skipped — so sibling `Facet`s get no data either. `AnswerResults` never fires
7. Facet fields must be `keyword` type in the schema — `text` fields produce meaningless facet values
8. The provider does not sync URL state, but `fromUrlQueryString` / `toUrlQueryString` are exported for wiring it up through `onChange`
