---
name: sync-s3-to-antfly
description: Ingest and validate content from Amazon S3, an S3-compatible store such as Cloudflare R2, Google Cloud Storage, or a local directory into Antfly (self-hosted or Antfly Cloud). Use when indexing private bucket content, defining a prefix, configuring read-only object credentials, ingesting documents or images, or diagnosing inaccessible, stale, or skipped objects.
---

# Sync S3 to Antfly

Connect the narrowest bucket scope that satisfies the knowledge use case.

Antfly has no native bucket-sync connector. Your ingestion job lists objects and writes
one Antfly document per object; Antfly then fetches each object's content through an
index template or document-extraction producer using server-side read credentials. On
Antfly Cloud, check whether the instance offers a hosted source for this provider before
building a job; that path is not verified here.

## Workflow

1. Record provider, S3 API endpoint, region behavior, bucket, and exact prefix.
2. Confirm the endpoint is the S3-compatible API endpoint, not a dashboard or public asset URL.
3. Create least-privilege credentials with list access to the prefix and read access to its
   objects. Keep them separate from any primary-storage credential, which grants database
   write authority.
4. Configure server-side read access (never commit credential values; use the keystore or
   secret references):
   - S3 / R2: `remote_content.s3` (named credentials can be selected by bucket); templates
     such as `remoteText` and `remoteMedia` then read `s3://` URLs.
   - GCS: a named `external_io` connection with the explicit `content.fetch` capability and
     a source-only bucket/prefix scope; `objects.read` alone does not authorize downloads.
   - Local files: `file://` reads are denied unless
     `remote_content.security.allowed_paths` lists a dedicated ingestion directory.
   Keep `remote_content` host/object allowlists narrow; an omitted allowlist leaves
   template fetches unrestricted.
5. Create the destination table and indexes before the first load: full text, an
   embeddings index with a `chunker` for text, document extraction for PDFs and scans, or a
   media template for images.
6. List the prefix and batch-insert one document per object, keyed by the object key, with
   the object URL, content type, ETag/version, and modification time. Report discovered,
   written, skipped, and failed counts.
7. Wait for enrichment: `antfly index wait --table T --index I --until complete`.
8. Sample stored documents and verify source path, content type, text or media field, and modification metadata.
9. Run known-positive retrieval tests and an update/delete refresh test (re-insert changed
   objects; delete removed keys).

## Images

Object discovery does not by itself create visual search. Store a retrievable
media reference, use a supported multimodal embeddings model/index, and test a
concrete visual description. Private image previews require a separate signed
URL or application proxy; successful embedding does not make an object public.

See `references/r2.md` when using Cloudflare R2.
