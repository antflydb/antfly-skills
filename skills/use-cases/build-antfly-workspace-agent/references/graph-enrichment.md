# Optional graph enrichment in Antfly

Keep three capabilities separate:

1. **Graph index:** Antfly stores explicit edges and answers bounded traversal queries.
2. **Extraction model:** GLiNER2 reads text and proposes entities/relationships.
3. **Projection:** validated source-backed candidates become indexed edges.

A connected model listing does not prove inference works. Test the advertised model with
a small synthetic extraction request. Verify actual entities, directional relations and source
spans before ingesting private derived assertions. Keep inference and graph storage in Antfly
where available; an additional graph database is not required.

A general Workspace graph can connect people, projects, documents, messages, meetings and
calendar events. Prefer exact native relationships (thread membership, document links,
calendar conference IDs) where available. Model-inferred relations require provenance and
uncertainty labels. An invited attendee is not confirmed attendance; a suggested task is not
an accepted commitment. Every returned relation inherits its evidence's access requirements.

Test graph storage with an isolated synthetic fixture and exact expected paths. Separately
test GLiNER2, projection and retrieval over the actual corpus. Do not claim that an isolated
graph test demonstrates a working private knowledge graph.

The Antfly pilot previously passed native graph indexing/traversal tests, but GLiNER2 model
loading returned `MODEL_LOAD_FAILED` / `CudaUnavailable`; the advertised shared quantized
variant returned 502. Recheck current status and diagnose the selected route/worker. Do not
change unrelated local inference settings based only on a shared connection screenshot.

When extraction is unavailable, keep the general agent usable through verified search and
show graph enrichment as unavailable. Add embeddings or deterministic source-link edges only
after their own readiness checks. Graph enrichment improves the retrieval path; it does not
define the product or force a decision ontology.
