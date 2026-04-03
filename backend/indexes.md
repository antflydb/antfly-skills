# Indexes — Full-Text, Embeddings, Graph

Indexes are attached to tables and determine what kinds of queries are possible. A table can have multiple indexes of different types.

## Full-Text Index (BM25)

Type: `full_text`

Powered by Bleve. Provides keyword search with TF-IDF/BM25 relevance scoring.

**How it works**: If the table has a JSON Schema with `x-antfly-types`, field mappings are generated automatically. Without a schema, documents are dynamically indexed.

**Supports**: text, keyword, numeric, boolean, datetime, geopoint, search_as_you_type field types.

**Query syntax**: Bleve query DSL — match, term, phrase, fuzzy, prefix, wildcard, numeric_range, date_range, geo_distance, conjuncts (AND), disjuncts (OR). See [search.md](search.md).

**Config**: Minimal — just name and type. Field behavior comes from the schema.

## Embeddings Index (Vector Search)

Type: `embeddings`

This is where Antfly's semantic search comes from. Each embeddings index defines:

1. **Template** — a handlebars template that produces the text (or multimodal content) to embed
2. **Embedder** — which embedding model/provider to use
3. **Chunker** (optional) — how to split long documents into chunks before embedding

### Templates

The template runs against each document to produce the input for the embedding model:

- Text: `{{title}} {{content}}` — concatenates fields
- Multimodal: `{{media url=image_url}}{{caption}}` — embeds image + text together (CLIP models)
- Selective: `{{#if category}}Category: {{category}}. {{/if}}{{description}}` — conditional inclusion

Templates must reference fields that exist in the document. Missing fields produce empty strings.

### Embedding Providers

| Provider | Config key | Notes |
|----------|-----------|-------|
| Termite | `termite` | Local ONNX inference. Models: bge-small-en-v1.5, mxbai-embed-large-v1 |
| Ollama | `ollama` | Local. Models: nomic-embed-text, all-minilm, mxbai-embed-large |
| OpenAI | `openai` | API. Models: text-embedding-3-small, text-embedding-3-large |
| Google Gemini | `gemini` | API. Models: gemini-embedding-001 |
| Google Vertex | `vertex` | Enterprise API |
| AWS Bedrock | `bedrock` | Enterprise API |

Dimension is auto-detected from the provider if not specified.

### Chunking

For long documents, configure a chunker to split content before embedding:

- `target_tokens` — chunk size (e.g., 512)
- `overlap_tokens` — overlap between chunks (e.g., 50)
- Chunker models: `fixed-bert-tokenizer`, `fixed-bpe-tokenizer`, or Termite semantic chunker

Each chunk gets its own embedding vector. Search returns the most relevant chunk(s).

### Distance Metrics

- `l2_squared` (default) — Euclidean distance
- `cosine` — cosine similarity
- `inner_product` — dot product

### Quantization

RaBitQ quantization available for vector compression. Reduces memory usage significantly.

### Multiple Indexes

A table can have multiple embeddings indexes (e.g., one for title, one for full content, one for images). Queries specify which index to search via the `indexes` parameter.

## Graph Index

Type: `graph`

Defines edge types between documents, enabling traversal queries.

**Config**: List of edge types, each with a name and the field that contains the edge values.

**Example**: An edge type `mentions_entity` on field `entities` creates edges from a document to every entity it mentions. Query with graph traversal to find connected documents.

## Remote Index

Type: `remote`

Proxy index that forwards queries to an external search service. Useful for federated search.

## Enrichments

Enrichments are the async pipeline that runs when documents are written. They use indexes to generate derived data:

- **Embedding enrichment**: Generates embedding vectors using the embeddings index config
- **Summary enrichment**: Generates text summaries using an LLM
- **Graph enrichment**: Extracts entities and creates graph edges

Enrichments run in background after the document is committed to Raft. The `sync_level` parameter controls how long to wait:
- `propose` — return immediately after Raft proposal (enrichments run async)
- `aknn` — wait for vector index to be updated before returning

## Sharp Edges

1. **`indexes` parameter is required for semantic queries** — `semantic_search` without `indexes: ["index_name"]` silently returns zero results. No error.
2. Embedding dimension is auto-detected but can be overridden. Mismatched dimensions cause write failures.
3. Handlebars template must reference existing document fields — typos in field names produce empty embeddings.
4. `sync_level: "aknn"` is required to query vector results immediately after writing. Default `propose` is fast but vector index may not be updated yet.
5. Multiple embedding indexes per table are supported but each must have a unique name.
6. Changing an embedding model after data is loaded requires re-indexing all documents (embeddings are model-specific).
