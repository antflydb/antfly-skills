# Antfly — Frontend Skill

## What Exists

Antfly provides two frontend packages:

- **`@antfly/sdk`** (npm) — TypeScript client for the Antfly REST API. Full CRUD, queries, streaming RAG.
- **`@antfly/components`** (npm) — React component library that wires directly to an Antfly backend. Search UIs, RAG/Q&A, facets, autocomplete — all pre-built.

These are separate packages. `@antfly/components` depends on `@antfly/sdk` as a peer dependency.

## How Components Connect

```
<Antfly url="..." table="..." headers={...}>     ← Provider: sets API URL, table, auth
  <QueryBox id="search" mode="live">              ← Input: captures search text
    <Autosuggest fields={["title"]} />             ← Dropdown: autocomplete suggestions
  </QueryBox>
  <Facet id="cat" fields={["category.keyword"]} />← Sidebar: faceted filtering
  <Results                                         ← Output: renders search hits
    id="results" searchBoxId="search"
    fields={["title"]} semanticIndexes={["emb"]}
    items={(hits) => hits.map(h => <Card {...h} />)}
  />
</Antfly>
```

Everything inside `<Antfly>` shares state via context. QueryBox captures input, Facet adds filters, Results/RAGResults/AnswerResults display output. The `<Antfly>` provider coordinates queries automatically — components don't call the API directly.

## Skill Modules

- [sdk.md](sdk.md) — TypeScript SDK: client init, auth, queries, streaming, types
- [components.md](components.md) — React components: every component, its props, how they wire together
- [hooks.md](hooks.md) — React hooks: useAnswerStream, useSearchHistory, useCitations
- [patterns.md](patterns.md) — UI recipes: search page, Q&A chat, faceted catalog, custom input

## Critical Sharp Edges

1. `<Antfly>` provider is **required** — all components must be descendants of it
2. `semanticIndexes` must be passed to `<Results>` or `<AnswerResults>` for vector search — same rule as the API
3. `@antfly/components` requires `react` 16-19 and `@antfly/sdk` as peer dependencies
4. Import stylesheet: `import '@antfly/components/dist/components.css'` — without this, components render unstyled
5. `mode="live"` on QueryBox searches as you type; `mode="submit"` waits for enter/button click — choose based on UX (search vs Q&A)
6. `searchBoxId` on Results/RAGResults/AnswerResults must match the `id` on the QueryBox that drives it
7. Facet fields must be `keyword` type in the schema — `text` fields produce meaningless facet values
