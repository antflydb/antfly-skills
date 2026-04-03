# Integrations — CDC, S3, Document Sync

## CDC from PostgreSQL

Antfly can replicate data from PostgreSQL in real-time using logical replication.

**How it works**:
1. Postgres publishes WAL changes via a logical replication slot
2. Antfly subscribes and applies changes (inserts, updates, deletes) to an Antfly table
3. Enrichments (embeddings, summaries) are auto-generated on replicated data

**Requirements**:
- PostgreSQL `wal_level = logical` (must be set in postgres.conf, requires restart)
- A publication on the source table(s)
- Antfly configured with Postgres connection details

**Use case**: Keep a searchable copy of Postgres data with semantic search and RAG capabilities, without changing the source application.

See `/docs/guides/cdc-replication.mdx` for configuration details.

## S3/R2 Storage Backend

Antfly can use S3-compatible storage (AWS S3, Cloudflare R2, MinIO) as the backing store for shard data.

**Benefits**:
- ~87% storage cost reduction vs local NVMe
- 100-1000x faster shard splits (reference existing files, no copy)
- Single S3 copy instead of 3x replication (only Raft leader writes; followers read shared objects)

**Compatible services**: AWS S3, Cloudflare R2, MinIO, any S3-compatible API.

**Configuration**: endpoint, region, bucket, prefix, credentials (via env vars or keystore).

See `/docs/s3-storage.md` for setup guide.

## Document Sync (DocsAF)

Antfly includes document ingestion connectors for various sources:

| Source | Description |
|--------|-------------|
| Filesystem | Watch a directory, sync files into Antfly |
| Web Crawl | Crawl a website, index pages |
| Git | Index a git repository's contents |
| Google Drive | OAuth-based folder sync |
| S3/R2 | Import documents from object storage |

DocsAF uses LinearMerge internally — sorted records, cursor-based, with orphan cleanup.

## Webhooks

Event notifications on document changes. Configure webhook URLs to receive callbacks when documents are inserted, updated, or deleted.

## Sharp Edges

- CDC requires Postgres `wal_level = logical` — this is a server-level setting, not per-database. Requires Postgres restart.
- S3 credentials: prefer environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) or Antfly keystore (`${secret:aws.access_key_id}`). Never hardcode credentials.
- Document sync connectors use LinearMerge pattern — large imports may take time due to sorted-key requirement and enrichment processing.
- S3 storage reduces local disk needs but adds network latency for reads. Best for cost optimization, not lowest-latency reads.
