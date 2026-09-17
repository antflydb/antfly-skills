# Library roadmap

## Current library

The library contains the flagship `antfly` skill, 13 focused Skills, and three
Guides. The Documentation Support Agent Guide is in preview; the Workspace
and Google Agent Guides are experimental. See [the catalog](../catalog.yaml)
for the current inventory.

## Before promoting Guides to verified

- Record supported Antfly and harness versions and live smoke-test results.
- Run retrieval, citation, failure, and permission-boundary evaluations.
- Replace provisional compatibility text with tested release versions.
- Verify installed packages and their references outside this checkout.

## Validation improvements

- Compare required and denied tools with discovered MCP capabilities.
- Validate canonical query patterns against the connected server.
- Run known-positive semantic and hybrid retrieval fixtures.
- Confirm read-only keys hide mutation and administration tools.
- Track connection, retrieval, fallback, and complete-answer latency.

## Candidate additions

These are possible directions, not release commitments. Propose and track
specific work in [issues](https://github.com/antflydb/antfly-skills/issues).

- A first-success walkthrough from connection to a grounded answer.
- More troubleshooting recipes and environment configuration examples.
- OpenAI Agents SDK support, plus website and PostgreSQL connectors.
- Guides for retrieval assessment and agent memory.
- Guide catalog integration in the Antfly UI, including setup and verification.
