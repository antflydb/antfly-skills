# Antfly Documentation Support Agent

Build a grounded documentation support agent with Antfly retrieval.

Use Antfly as the evidence and retrieval layer for a support experience in an
agent harness or web application.

## Outcome

The completed agent answers product and technical questions from retrieved
documentation, links claims to public sources, declines unsupported claims,
and escalates deterministically when evidence is insufficient.

## Before you begin

You need:

- an Antfly Cloud instance;
- a documentation source in GitHub or S3-compatible storage;
- a document table with full-text and embeddings indexes;
- a dedicated read-only API key;
- one supported agent harness.

## Guided path

1. Choose `sync-github-to-antfly` or `sync-s3-to-antfly` and verify ingestion.
2. Use `query-antfly` to test a broad semantic query and an exact-term hybrid query.
3. Use `connect-antfly-mcp` to verify the read-only tool boundary.
4. Choose the Codex, Claude Code, n8n, or Copilot harness skill.
5. Use `build-antfly-support-agent` to apply grounding, citation, fallback, and escalation rules.
6. Run the portable evaluation set and harness-specific direct-chunk regression before publishing.

## Successful completion

- Normal operation exposes only `query` and `get_document`.
- One intent-selected retrieval call is the default; one focused fallback is the maximum.
- Answers are built from explanatory chunk text rather than filenames or scores.
- Citations resolve to public documentation URLs.
- Authentication, authorization, and transport failures never trigger model-driven retry loops.

The Next.js applications remain Starters: use them when a hosted support UI is
needed, not as the canonical definition of support-agent behavior.

This Guide is the complete customer outcome package. Its instructions are the
human-facing experience, and its Skills are the agent-facing procedures.
