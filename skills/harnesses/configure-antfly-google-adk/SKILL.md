---
name: configure-antfly-google-adk
description: Build and verify a Google ADK agent using Gemini on Vertex AI and Antfly MCP retrieval, with optional private Cloud Run deployment. Use for Google agent runtime setup, Google Cloud authentication, MCP tools, grounded answers and deployment; source ingestion is a separate workflow.
---

# Configure Antfly for Google ADK

Google ADK orchestrates the agent, Gemini on Vertex AI generates responses, and Antfly
provides indexed evidence over MCP. This runtime pattern works with any authorized Antfly
dataset. Workspace, BigQuery and other sources use separate ingestion procedures.

## Local runtime and retrieval

1. Discover the existing app, dependency lock, Google project, Vertex location/model and
   Antfly endpoint/table. Preserve a working SDK version rather than migrating incidentally.
2. Read `references/runtime-and-mcp.md`. Verify application-default credentials for local
   Vertex calls; CLI login alone does not establish ADC. Use an attached service identity in
   Cloud Run. Google Cloud authentication does not grant user-source access.
3. Compose `connect-antfly-mcp` when available. Initialize the exact MCP endpoint, discover
   schemas and test a known query and source lookup with a dedicated read-only credential.
4. Expose bounded retrieval through a trusted ADK tool adapter. Construct table and mandatory
   scope filters outside model arguments. For private corpora, enforce original-source access
   before returning text or metadata to the model. A tool allowlist alone is insufficient.
5. Apply `assets/grounding-instructions.md`. Bound model/tool calls, result sizes and runtime;
   close runners and MCP sessions. Distinguish empty evidence from transport/auth failures.
6. Exercise an actual agent turn, inspect explanatory passages and citations, then test
   unsupported questions, wrong scope and connection failures with `assets/google-agent-evals.json`.

## Hosting when requested

Read `references/cloud-run.md` for private deployment, Secret Manager, runtime identity,
IAP and verification. A custom UI is optional. Deployment authorization follows the user's
task scope; prepare the app and verify the build contents before any required final approval.

## Completion and reuse

Record SDK/model versions and distinguish connection discovery, MCP query, agent response,
source lookup, local tests and deployed tests. A REST adapter is a valid implementation
choice but does not verify an MCP path. Do not substitute local search after Antfly failure.

Graph extraction and hybrid search depend on separately verified Antfly models/indexes.
Neither is a Google runtime prerequisite. Keep source-specific permissions and business
actions in their own adapters; an agent must not acquire write privileges to fix retrieval.

This package provides reusable procedures and evaluations derived from earlier Google-stack
builds. It does not bundle their private configuration or imply every new dataset is connected.
