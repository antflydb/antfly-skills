---
name: sync-s3-to-antfly
description: Configure and validate an Amazon S3 or S3-compatible object store such as Cloudflare R2 as an Antfly Cloud knowledge source. Use when indexing private bucket content, defining a prefix, storing S3 credentials, ingesting documents or images, or diagnosing inaccessible, stale, or skipped objects.
---

# Sync S3 to Antfly

Connect the narrowest bucket scope that satisfies the knowledge use case.

## Workflow

1. Record provider, S3 API endpoint, region behavior, bucket, and exact prefix.
2. Confirm the endpoint is the S3-compatible API endpoint, not a dashboard or public asset URL.
3. Create least-privilege credentials with list access to the prefix and read access to its objects.
4. Store credentials in Antfly Cloud's connector secret facility; never commit them.
5. Select the destination table and configure file-type inclusion before the first sync.
6. Run ingestion and inspect discovered, extracted, skipped, and failed counts.
7. Sample stored documents and verify source path, content type, text or media field, and modification metadata.
8. Wait for the required full-text, embeddings, or multimodal enrichment to become queryable.
9. Run known-positive retrieval tests and an update/delete refresh test.

## Images

Object discovery does not by itself create visual search. Store a retrievable
media reference, use a supported multimodal embeddings model/index, and test a
concrete visual description. Private image previews require a separate signed
URL or application proxy; successful embedding does not make an object public.

See `references/r2.md` when using Cloudflare R2.
