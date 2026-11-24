# Indexes — Full-Text, Embeddings, Graph, Algebraic, Relational

Indexes are attached to tables and determine what kinds of queries are possible. A table can have multiple indexes of different types. The index name is the key of the table's `indexes` map — do not repeat `name` inside the config.

Index types: `full_text`, `embeddings`, `graph`, `algebraic`, `relational`. Query-time access to *external* data is not an index type — see `foreign_sources` in [search.md](search.md).

## Full-Text Index (BM25)

Type: `full_text`

Keyword search with BM25 relevance scoring. The query-string grammar is a Lucene-style subset defined by `zig/QUERY_STRING.md` — not Elasticsearch parity (no Lucene-complete escaping, no multi-field expansion, no `simple_query_string`, no query-string `minimum_should_match`).

**How it works**: If the table has a JSON Schema with `x-antfly-types` / `x-antfly-field`, field mappings are generated automatically. Without a schema, documents are dynamically inferred.

**Supports**: text, html, keyword, numeric, boolean, datetime, geopoint, geoshape, link, search_as_you_type field types.

**Wire query keys**: `match`, `term` (with `fuzziness`/`prefix_length` for fuzzy), `fuzzy`, `terms` (phrase), `match_phrase`, `multi_match`, `prefix`, `wildcard`, `regexp`, `ids`, `match_all`, `match_none`, `query` (query-string), and `bool`/`conjuncts`/`disjuncts`. The remaining leaf types are discriminated by their own keys sitting beside `field`, not by a wrapper key: flat numeric/term/date ranges (`min`/`max` or `start`/`end`), `bool` with a boolean value for a boolean-field match (an *object* value under `bool` is the boolean query instead), `cidr` for IP ranges, `location` + `distance` for geo distance, `min_lat`/`min_lon`/`max_lat`/`max_lon` for a geo bounding box, and `polygon_points`/`geometry` for geo shapes. The wrapped `bool_field`, `ip_range`, `geo_distance`, and `geo_bbox` keys are `filter_query`/`exclusion_query` forms only. See [search.md](search.md).

**Config**: `mem_only` (memory-only storage), `field` (index one document field as text; omit for the table's default full-document index), and `artifact_name` (index a generated artifact stream). Field behavior otherwise comes from the schema.

## Embeddings Index (Vector Search)

Type: `embeddings`

Dense HBC (hierarchical balanced clustering) by default, or LEANN with `algorithm: "leann"`; `sparse: true` creates a SPLADE inverted index instead. Each managed embeddings index defines:

1. **Source** — a `field` to embed, or a handlebars `template` producing the text/multimodal content
2. **Embedder** — which embedding model/provider to use
3. **Chunker** (optional, managed dense **or** sparse) — how to split long documents into chunks before embedding

A `summarizer` key is **rejected outright** on an embeddings index (`UnsupportedCreateTableRequest`) — `summarizer` exists only on graph indexes, where it generates node summaries.

Set `external: true` to supply vectors yourself via `_embeddings`; then no field, template, or embedder is allowed.

### Templates

The template runs against each document to produce the embedding input:

- Text: `{{title}} {{content}}` — concatenates fields
- Multimodal: `{{media url=image_url}}{{caption}}` — embeds image + text together (the embedder must accept images; see `inputs` below)
- Selective: `{{#if category}}Category: {{category}}. {{/if}}{{description}}` — conditional inclusion

Templates must reference fields that exist in the document. Missing fields produce empty strings.

### Embedding Providers

`EmbedderProvider`: `antfly`, `bedrock`, `cloudflare`, `cohere`, `gemini`, `vertex`, `ollama`, `openai`, `openrouter`. There is no `anthropic` embedder.

| Provider | Config key | Notes |
|----------|-----------|-------|
| Antfly inference | `antfly` | Built-in local runtime (GGUF, safetensors, or ONNX artifacts on Antfly's own CPU/Metal/CUDA kernels), loaded from `models/embedders/{name}/`. Accepts text, image, and audio inputs |
| Ollama | `ollama` | Local. e.g. nomic-embed-text (768d), mxbai-embed-large (1024d) |
| OpenAI | `openai` | `text-embedding-3-small` (1536d), text-embedding-3-large (3072d). `dimensions` for MRL reduction |
| OpenRouter | `openrouter` | OpenAI-compatible; defaults to the OpenRouter endpoint |
| AWS Bedrock | `bedrock` | AWS credential chain. e.g. `cohere.embed-v4`, `amazon.titan-embed-text-v2:0`. `request_format` ∈ `auto` (default), `titan_text`, `titan_multimodal`, `cohere_v3`, `cohere_v4`. Accepts text and image |
| Gemini / Vertex | `gemini` / `vertex` | `request_format` and `task_encoding` (`prompt` \| `task_type` \| `none`) are Google-only |
| Cohere | `cohere` | `retrieval.query_input_type` / `document_input_type` |
| Cloudflare Workers AI | `cloudflare` | `account_id`, optional `gateway_id` |

The embedder validator requires a non-empty `model` for every provider except `antfly`.

**Input types**: the removed `multimodal` flag is replaced by `inputs` (`["text", "image", "audio"]`).
Normally omit it — Antfly discovers what the model accepts. Set it only for a model whose capabilities
Antfly cannot discover; it then replaces the discovered set. Only `antfly` (image, audio) and
`bedrock` (image) accept media inputs; other providers reject them. A stored `multimodal` value is
ignored.

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

### Algorithm and Quantization

Dense indexes use RaBitQ codes. These fields are fixed when the index is created:

- `algorithm` — `hbc` (default; quantized codes plus full-precision rerank data) or `leann` (a pruned
  proximity graph plus compact codes; recomputes exact distances for a few candidates per query by
  re-embedding or reading stored embeddings — smaller index, more query-time work). LEANN does not yet
  support shard splits or native index backups.
- `quantization_bits` — 1–8 bits per dimension. HBC default 1; above 1 stores extended codes used to
  rescore candidates (better recall, ~`dims * bits / 8` extra bytes per vector). LEANN default 4 with
  the `rabitq` quantizer; `pq` allows only 1.
- `quantization_refine` — HBC with `quantization_bits > 1` only: `near_cutoff` (default; rescore only
  candidates that could still enter the results) or `all`. Not allowed with `leann`.
- `leann` — tuning block for `algorithm: "leann"`: `max_degree` (4–128, default 30), `quantizer`
  (`rabitq` default \| `pq`), `vector_storage` (`auto` \| `transient` \| `persistent`), `search_ef`,
  `bound_scale`, `batch_size`.

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

## Relational Index

Type: `relational`

A schema-bound composite ordered index on a **relational table** (typed rows, see the relational row
APIs): `keys` (1–32), each with its own direction, null placement, and string collation. Existing rows
build asynchronously; indexed queries need complete coverage. The table schema is the durable
authority for these definitions. Not used on document tables.

## Index Aliases

`PUT|GET|DELETE /db/v1/tables/{table}/index-aliases/{alias}` (also under
`/db/v1/databases/{db}/namespaces/{ns}/tables/{table}/...`) gives a stable name that points at one
concrete index, so applications can switch embedding models without changing the index name in
queries.

```json
PUT /db/v1/tables/docs/index-aliases/chunk_vectors
{ "index": "chunk_vectors_v2", "expected_index": "chunk_vectors_v1", "require": "complete", "idempotency_key": "upgrade-v2" }
```

- Create by omitting `expected_index`; swap by supplying the exact current target (stale → 409).
- `require`: `complete` (default) or `queryable` (also accepts partial serving). A swap rejects an
  unready target, a different index kind, or a dense/sparse mismatch.
- Aliases cannot shadow a concrete index or point at another alias.
- Use the alias anywhere an index name goes: `indexes`, `full_text_index`, embedding map keys,
  `graph_queries` `index`, graph metric requests. Resolution happens before embedding, and the alias
  selects the query embedder together with the index. Results carry `resolved_indexes`.
- `DELETE` requires `If-Match` with the ETag from `GET` (missing → 428, stale → 412). Physical
  indexes are untouched.
- Mutations need table admin; `GET` needs table read. Retry an ambiguous `PUT` with the identical
  body and `idempotency_key`. Limit 64 aliases per table.
- Distributed clusters: upgrade every metadata and data node before using aliases.

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
- `query` (alias `full_text`) — waits for full-text query visibility only; enrichments still run in the background
- `enrichments` — waits for this write's enrichment publication. Precomputing before commit (where a producer failure rejects the write) is selected by `commit_requires: "direct_enrichments"`; when `commit_requires` is omitted, embedded `enrichments`/`full_index` writes keep the legacy precompute during the migration window. See [data.md](data.md#sync-levels)
- `full_index` — waits for all of **that write's own** derived effects, vector indexes included. It does not wait on corpus-wide backfill of a newly created index

## Sharp Edges

1. **`indexes` is required for semantic queries** — `semantic_search` without a resolvable index is rejected with **HTTP 422** (`unsupported query request`), not an empty result set.
2. Embedding dimension is auto-detected by probing the embedder; external dense indexes must declare it. A stored index whose dimension no longer matches its config fails to open (`DimensionMismatch`); an embedder returning the wrong width fails the write (`InvalidEmbeddingDimensions`).
3. Handlebars templates must reference existing document fields — a field missing from the document renders as an empty string.
4. `sync_level: "full_index"` is required to query vector results immediately after writing — for that write only, not for a new index still backfilling. `"aknn"` is a removed alias and servers reject it.
5. Multiple embedding indexes per table are supported, but the map key (the index name) must be unique.
6. Changing an embedding model: either `DELETE` the index and `POST` it again (re-enriched in the background), or create a new index beside it and swap an [index alias](#index-aliases) once it is ready, which avoids a gap in serving.
7. There is no `remote` index type. Query-time federation is `foreign_sources` on the query request.
