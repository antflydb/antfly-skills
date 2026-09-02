# Indexes — Full-Text, Embeddings, Graph, Algebraic

Indexes are attached to tables and determine what kinds of queries are possible. A table can have multiple indexes of different types. The index name is the key of the table's `indexes` map — do not repeat `name` inside the config.

Index types: `full_text`, `embeddings`, `graph`, `algebraic`. Query-time access to *external* data is not an index type — see `foreign_sources` in [search.md](search.md).

## Full-Text Index (BM25)

Type: `full_text`

Keyword search with BM25 relevance scoring. The query-string grammar is a Lucene-style subset defined by `zig/QUERY_STRING.md` — not Elasticsearch parity (no Lucene-complete escaping, no multi-field expansion, no `simple_query_string`, no query-string `minimum_should_match`).

**How it works**: If the table has a JSON Schema with `x-antfly-types` / `x-antfly-field`, field mappings are generated automatically. Without a schema, documents are dynamically inferred.

**Supports**: text, html, keyword, numeric, boolean, datetime, geopoint, geoshape, link, search_as_you_type field types.

**Wire query keys**: `match`, `term` (with `fuzziness`/`prefix_length` for fuzzy), `fuzzy`, `terms` (phrase), `match_phrase`, `multi_match`, `prefix`, `wildcard`, `regexp`, `ids`, `match_all`, `match_none`, `query` (query-string), and `bool`/`conjuncts`/`disjuncts`. The remaining leaf types are discriminated by their own keys sitting beside `field`, not by a wrapper key: flat numeric/term/date ranges (`min`/`max` or `start`/`end`), `bool` with a boolean value for a boolean-field match (an *object* value under `bool` is the boolean query instead), `cidr` for IP ranges, `location` + `distance` for geo distance, `min_lat`/`min_lon`/`max_lat`/`max_lon` for a geo bounding box, and `polygon_points`/`geometry` for geo shapes. The wrapped `bool_field`, `ip_range`, `geo_distance`, and `geo_bbox` keys are `filter_query`/`exclusion_query` forms only. See [search.md](search.md).

**Config**: `mem_only` (memory-only storage), `field` (index one document field as text; omit for the table's default full-document index), and `artifact_name` (index a generated artifact stream). Field behavior otherwise comes from the schema.

## Embeddings Index (Vector Search)

Type: `embeddings`

Dense HBC (hierarchical balanced clustering) by default; `sparse: true` creates a SPLADE inverted index instead. Each managed embeddings index defines:

1. **Source** — a `field` to embed, or a handlebars `template` producing the text/multimodal content
2. **Embedder** — which embedding model/provider to use
3. **Chunker** (optional, managed dense **or** sparse) — how to split long documents into chunks before embedding

A `summarizer` key is **rejected outright** on an embeddings index (`UnsupportedCreateTableRequest`) — `summarizer` exists only on graph indexes, where it generates node summaries.

Set `external: true` to supply vectors yourself via `_embeddings`; then no field, template, or embedder is allowed.

### Templates

The template runs against each document to produce the embedding input:

- Text: `{{title}} {{content}}` — concatenates fields
- Multimodal: `{{media url=image_url}}{{caption}}` — embeds image + text together
- Selective: `{{#if category}}Category: {{category}}. {{/if}}{{description}}` — conditional inclusion

Templates must reference fields that exist in the document. Missing fields produce empty strings.

### Embedding Providers

Index creation accepts **four** providers. Anything else — including spec-enum values such as gemini, vertex, openrouter, cohere, and anthropic — is rejected with `UnsupportedEmbeddingProvider`, even though the OpenAPI enum is wider.

| Provider | Config key | Notes |
|----------|-----------|-------|
| Antfly inference | `antfly` | Built-in local ONNX inference, loaded from `models/embedders/{name}/`. e.g. bge-base-en-v1.5 (768d), all-MiniLM-L6-v2 (384d) |
| Ollama | `ollama` | Local. e.g. nomic-embed-text (768d), mxbai-embed-large (1024d), all-minilm (384d) |
| OpenAI | `openai` | `text-embedding-3-small` (1536d), text-embedding-3-large (3072d). `dimensions` for MRL reduction |
| AWS Bedrock | `bedrock` | AWS credential chain. e.g. `cohere.embed-v4`, `amazon.titan-embed-text-v2:0`. `request_format` ∈ `auto` (default), `titan_text`, `titan_multimodal`, `cohere_v3`, `cohere_v4` |

A **non-empty `model` is required for every provider** — no default is ever substituted. The per-provider `default` values in the spec are annotations on a required field, so an empty or missing model fails the create with `InvalidCreateTableRequest`.

There is no `termite` provider — local inference is `antfly`.

`dimension` is auto-detected for managed dense indexes by probing the configured embedder. It is **required** for external dense indexes, and ignored for sparse ones.

### Chunking

For long documents, configure a chunker to split content before embedding:

```json
{
  "chunker": {
    "provider": "antfly",
    "model": "fixed_bert",
    "store_chunks": true,
    "text": { "target_tokens": 512, "overlap_tokens": 50 }
  }
}
```

- Provider is `antfly` (or `mock`)
- `model` is an open string. Omit it on an `antfly` chunker and create-time normalization **injects** `"model": "fixed"` into the stored config — both index-create paths (table create and index config) run the same normalizer, so what you read back is not what you sent. Note that `fixed` is not one of the chunkers `/ai/v1/models` advertises (`fixed_bert`, `fixed_bpe`), so an omitted model is not the same as picking a built-in one. Supply the name you actually want; anything other than the advertised built-ins loads from `models/chunkers/{name}/`. (Explicit values, `null` included, are preserved so validation can reject them)
- `target_tokens`, `overlap_tokens`, and `separator` nest under `chunker.text`; audio options nest under `chunker.audio`
- `store_chunks: false` (default) keeps chunks in memory and stores only embeddings
- `chunker.full_text_index` is an **object**, and only its presence matters: when present (even empty `{}`), chunk artifacts are persisted and routed into the table's default full-text index; when absent they feed vectors only, unless `store_chunks: true` persists them. Distinct from the enrichment-level `full_text_index`, a **boolean** on a chunk or asset enrichment that routes generated text into the table's default full-text index

Each chunk gets its own embedding vector. Search returns the most relevant chunk(s).

### Distance Metrics

- `cosine` (default) — cosine similarity (CLIP, OpenAI-style models). Omitting `distance_metric` on a managed embeddings index yields `cosine`; the spec's `l2_squared` default is overridden by the create translation
- `l2_squared` — Euclidean distance
- `inner_product` — dot product

### Quantization

RaBitQ quantization is applied automatically as an internal storage format for vector compression — there is no quantization field on the index config to set.

### Multiple Indexes

A table can have multiple embeddings indexes (e.g. one for title, one for full content, one for images). Queries specify which to search via `indexes`.

## Graph Index

Type: `graph`

Defines edge types between documents, enabling traversal queries.

**Config**: `edge_types` — a list of entries from which the engine reads only `{name, field, topology}`; `name` is required and `topology` defaults to `graph` (the alternative is `tree`). The API allow-list also accepts `max_weight`, `min_weight`, `allow_self_loops`, and `required_metadata` per entry, plus `max_edges_per_document` on the index — these are type-checked at create time and then **silently ignored** by the engine. Optional `summarizer` + `template` generate node summaries, which is what enables tree navigation in the retrieval agent. `GraphIndexConfig` also accepts `artifact`, `nodes`, `edge`, `context`, `algebraic_planning`, and `resolvers`.

**Two edge source families**:
- **Artifact source** — `source` with `kind: "artifact"` (a `GraphArtifactSourceConfig`) materializes an artifact stream, e.g. extraction relations, into graph edges.
- **Document field** — edges come from the document's `_edges`, which `edge_types[].field` (a key or array of keys) normalizes into. `source` also accepts `kind: "document_field"`, whose `field` must be exactly `"_edges"` — any other value is `InvalidIndexConfig`.

Exclusivity is **per field, not per index**: an `edge_types` entry that declares `field` is rejected when an artifact `source` is present. Field-less `edge_types` entries alongside an artifact source are legal.

**Example**: an edge type `mentions_entity` on field `entities` creates edges from a document to every entity it mentions.

## Algebraic Index

Type: `algebraic`

A schema-derived sidecar (`derive_from_schema: true`). Documents project into symbolic facts (`docfact` for schema-declared fields, `pathfact` for schemaless paths) that the planner folds algebraically: terms, stats, range, histogram, and cardinality aggregations; dense-vector pruning from symbolic doc-id constraints; graph-traversal constraints; and derived joins. Materializations are engine-owned; there is no public field configuration.

## Enrichments

Enrichments are the managed pipeline that materializes generated artifacts before indexing. Kinds:

- `chunk` — split source text (or an asset artifact) into chunk artifacts
- `asset` — produce derived assets, e.g. extracted document pages
- `embedding` — produce embedding vectors from source rows or chunk artifacts

Summaries are not an enrichment kind — they come from `summarizer` on the embeddings or graph index config. Graph edges are not an enrichment kind either — they come from `GraphArtifactSourceConfig` on the graph index.

`sync_level` decides when enrichments run relative to the commit — it is not one monotonic ladder:
- `propose` (default) / `write` — enrichments run in the background after the commit
- `full_text` — waits for full-text publication only; enrichments still run in the background
- `enrichments` — enrichments are precomputed **synchronously before commit**; a producer failure rejects the write
- `full_index` — waits for all of **that write's own** derived effects, vector indexes included. It does not wait on corpus-wide backfill of a newly created index

## Sharp Edges

1. **`indexes` is required for semantic queries** — `semantic_search` without a resolvable index is rejected with **HTTP 422** (`unsupported query request`), not an empty result set.
2. Embedding dimension is auto-detected by probing the embedder; external dense indexes must declare it. A stored index whose dimension no longer matches its config fails to open (`DimensionMismatch`); an embedder returning the wrong width fails the write (`InvalidEmbeddingDimensions`).
3. Handlebars templates must reference existing document fields — a field missing from the document renders as an empty string.
4. `sync_level: "full_index"` is required to query vector results immediately after writing — for that write only, not for a new index still backfilling. `"aknn"` is a removed alias and servers reject it.
5. Multiple embedding indexes per table are supported, but the map key (the index name) must be unique.
6. Changing an embedding model means `DELETE` the index then `POST` it again with the new config; existing data is re-enriched automatically (asynchronously, in the background).
7. There is no `remote` index type. Query-time federation is `foreign_sources` on the query request.
