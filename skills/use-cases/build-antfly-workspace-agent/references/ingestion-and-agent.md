# Ingestion and the agent connection

## Antfly dataset

Normalize each source into a record with tenant/account, provider, provider resource ID,
title, body, source URL, event time, capture time, version/hash and access dependencies.
Create searchable passages with stable citation IDs and offsets or transcript timestamps.
Preserve structured Calendar dates/participants and email thread relationships for filtering.
Track duplicates as the same underlying event without treating their ACLs as interchangeable.

Ingest through Antfly's supported API or verified connector. Make source-version writes
idempotent; activate a version after index readiness, then retire old passages. Deny deleted,
revoked and stale records before serving answers. Cursor storage and scheduling belong to
connector orchestration; Antfly remains the search/index layer. Label a one-time import as
a snapshot rather than suggesting that a refresh button synchronizes source content.

Verify a known exact-term query, a cross-source topic query and a full source lookup.
Use full-text indexing first; verify embedding model/index readiness before claiming semantic
or hybrid search. Ingestion success is separate from successful retrieval.

## MCP boundary

Discover the exact hosted MCP URL and current tool schemas. Initialize Streamable HTTP,
list tools and execute one known query and source read. Keep ingestion/admin credentials
separate from runtime read-only credentials. Setup tools may inspect table/index capabilities;
normal model use exposes only bounded search and document lookup, commonly `query` and
`get_document`. Discover actual names and argument shapes. Treat MCP `isError` as failure.

Enforce table, account and original-source access outside model arguments. A raw instance-wide
query tool is unsuitable when it would expose other users' evidence or revoked sources.
Use a trusted tool adapter or authorized MCP gateway when source checks are not native to
the endpoint. Apply that same boundary to graph expansion and citation reads.

The chosen runtime consumes this retrieval contract:

- Input: user question, trusted caller scope, bounded optional time/source filters.
- Output: explanatory passages, citation IDs, original links, time/version locators and coverage.
- Failure: explicit unavailable/unauthorized/insufficient evidence; no invented replacement.

For Google ADK, configure its MCP toolset using Streamable HTTP and an available model;
verify the installed SDK against [ADK's MCP documentation](https://google.github.io/adk-docs/tools-custom/mcp-tools/).
For n8n, use its MCP Client Tool with stored credentials and explicit retrieval tool selection.
Other MCP clients can use the same contract. Authentication secrets stay in the runtime secret
store. Tool allowlisting is not a substitute for source authorization.

Test through the actual runtime and MCP connection. The current Antfly preview uses a direct
API adapter; those API tests do not certify MCP behavior. Preserve its source-access checks
when replacing the transport and rerun source lookup, errors and revocation cases.

## General agent experience

Accept ordinary questions instead of imposing Trace/Decide modes. Examples:

- What changed on this project across email, documents and meetings?
- Prepare a brief for tomorrow's meeting using its agenda and related source material.
- Find the latest specification and the discussion that explains it.
- What follow-ups were mentioned, and which have explicit owners?

Only offer Calendar-grounded meeting preparation after Calendar is ingested. Otherwise state
the narrower source scope. Cite claims, distinguish inferred relationships and uncertain
commitments, and make coverage/freshness visible. A model or UI can change without replacing
the Antfly dataset. Customer-specific downstream integrations belong in their implementation notes.
