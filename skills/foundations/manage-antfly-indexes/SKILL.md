---
name: manage-antfly-indexes
description: Plan, create, inspect, and safely change Antfly full-text, embeddings, multimodal, or graph indexes. Use when an Antfly table needs an index, enrichment is incomplete, semantic or visual search is unavailable, graph modeling is required, an embedding model must be swapped through an index alias, or index readiness must be verified.
---

# Manage Antfly Indexes

Treat index creation as a data contract and asynchronous lifecycle, not only a configuration call.

## Workflow

1. Describe the table and sample representative documents.
2. Select the index type from the query behavior required.
3. Verify every referenced field or template value exists in the stored documents.
4. For embeddings, choose a model compatible with the content modality and record its dimension when required.
5. Create a new index rather than destructively replacing a working index.
6. Wait for readiness and progressive enrichment until the intended corpus is queryable:
   `antfly index wait --table T --index I --until complete --timeout 10m`.
7. Test known-positive and known-negative queries against the new index.
8. Switch consumers only after evaluation passes. Prefer an index alias
   (`PUT /db/v1/tables/{table}/index-aliases/{alias}`), which atomically creates or swaps the
   target once it satisfies the readiness proof, so queries keep one index name across model changes.
9. Drop an old index only with explicit approval and a rollback plan.

## Index selection

- Full text: lexical matching, filters, facets, and exact terminology.
- Embeddings: semantic similarity over text or templates; add a `chunker` for long text.
- Multimodal embeddings: images/audio using a supported model and media template. Input
  modalities come from the model's discovered capabilities or an explicit `inputs` list; the
  old `multimodal` flag is ignored.
- Graph: explicit relationship extraction and traversal; define node/edge mappings before
  indexing. Extractor-fed graph indexes can use entity resolvers to merge repeated mentions.
- PDFs, scanned pages, and other documents: use native document processing (artifact
  extraction, OCR, chunking) rather than pre-extracting text; see upstream
  `docs/guides/index-documents.mdx` and `docs/guides/artifact-indexes.mdx`.

Never infer readiness only from successful index creation. Inspect status and run a query.
