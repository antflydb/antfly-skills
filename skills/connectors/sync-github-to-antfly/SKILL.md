---
name: sync-github-to-antfly
description: Ingest and validate a GitHub repository as an Antfly knowledge source (self-hosted or Antfly Cloud). Use when indexing documentation or repository content from GitHub, selecting branches and paths, scoping repository credentials, planning refresh behavior, or diagnosing stale and missing GitHub content in Antfly.
---

# Sync GitHub to Antfly

Load repository files into Antfly and prove that source changes become queryable evidence.

Antfly has no native GitHub connector. Your ingestion job (CI, a script, or a scheduled
worker) reads the repository and writes documents through the batch API.

## Workflow

1. Identify repository, branch, included paths, excluded paths, and supported file types.
2. Use a GitHub App or least-privilege token that can read only the required repositories.
   Keep it in the job's secret store; Antfly never needs it.
3. Create the destination table with an embeddings index over a template such as
   `{{path}} {{body}}` and a `chunker` (smaller chunks for code, for example
   `target_tokens: 150`), plus full text for exact symbols.
4. Insert one document per file, keyed by repository-relative path, with path, body,
   revision, and public URL metadata. Batch a few hundred files per request.
5. Wait for embedding to finish before the first query:
   `antfly index wait --table T --index I --until complete --timeout 10m`.
6. Sample documents to confirm title, body, source path, public URL, branch, and revision metadata.
7. Run one broad semantic and one exact-term hybrid query.
8. Commit a small source change, re-insert changed files (the index updates in place), delete
   removed paths, and verify update/delete behavior.
9. Record the job scope and last successful verification without storing credentials.

## Guardrails

- Exclude secrets, generated dependency trees, binaries, and private operational files.
- Do not assume repository URLs are suitable public citations; configure the intended public documentation base.
- Distinguish ingestion completion from downstream enrichment readiness.

See `references/source-contract.md` for recommended stored metadata.
