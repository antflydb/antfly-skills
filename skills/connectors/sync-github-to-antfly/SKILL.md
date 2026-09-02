---
name: sync-github-to-antfly
description: Configure and validate a GitHub repository as an Antfly Cloud knowledge source. Use when indexing documentation or repository content from GitHub, selecting branches and paths, setting connector credentials, planning refresh behavior, or diagnosing stale and missing GitHub content in Antfly.
---

# Sync GitHub to Antfly

Configure the product connector and prove that source changes become queryable evidence.

## Workflow

1. Identify repository, branch, included paths, excluded paths, and supported file types.
2. Use a GitHub App or least-privilege token that can read only the required repositories.
3. Create or select the Antfly destination table and define stable document keys from repository path and revision.
4. Configure extraction, chunking, full-text indexing, and the embeddings index.
5. Run the initial sync and inspect failed/skipped objects before querying.
6. Sample documents to confirm title, body, source path, public URL, branch, and revision metadata.
7. Run one broad semantic and one exact-term hybrid query.
8. Commit a small source change, refresh, and verify update/delete behavior.
9. Record the connector scope and last successful verification without storing credentials.

## Guardrails

- Exclude secrets, generated dependency trees, binaries, and private operational files.
- Do not assume repository URLs are suitable public citations; configure the intended public documentation base.
- Distinguish connector completion from downstream enrichment readiness.

See `references/source-contract.md` for recommended stored metadata.
