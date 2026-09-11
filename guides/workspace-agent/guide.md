# Google Workspace Agent with Antfly

Connect an agent to your organization's Workspace knowledge through Antfly.

**Google Workspace → Antfly ingestion and indexing → MCP → your agent**

The agent can answer questions, find relevant material, summarize projects and prepare
meeting briefs across the selected dataset. It is not tied to a decision workflow,
a particular model, a custom UI or an internal knowledge system.

## Sources

| Source | What the agent can use |
| --- | --- |
| Google Drive | Documents and supported files, with source links and versions |
| Gmail | Selected messages and threads |
| Google Meet | Available transcripts with time locators |
| Google Calendar | Events, agendas, participants and links to related resources |

Select sources and ingestion scope explicitly. Connecting one service does not authorize
or ingest the others. Further Workspace sources need their own connector and content checks.

## Build the pattern

1. **Set up Workspace access.** Authorize the selected account and source-read scopes.
   Verify actual content reads, including transcript availability and Calendar event access.
2. **Ingest into Antfly.** Preserve identity, timestamps, versions, source links and access
   dependencies. Index explanatory passages and verify search and document lookup.
   Choose a fixed snapshot or continuous synchronization, and show which is implemented.
3. **Connect through MCP.** Discover the endpoint and tool schemas. Use a read-only
   credential and enforce source access before retrieved content reaches the model.
4. **Choose the agent runtime.** Google ADK, n8n or another MCP client uses the same Antfly
   dataset. Apply grounding, citation and bounded tool-use rules in the chosen runtime.
5. **Verify cross-source answers.** Test normal questions, source links, missing evidence,
   changed/deleted content and access revocation through the actual agent connection.

Use [build-antfly-workspace-agent](../../skills/use-cases/build-antfly-workspace-agent/SKILL.md)
for the executable procedure and source-specific setup.

For the Google runtime, compose the [Google Agent Guide](../google-agent/guide.md), which
covers ADK, Vertex AI, Antfly MCP and optional private Cloud Run deployment.

## Example questions

- What changed on Project Atlas across email, documents and meetings?
- Prepare me for tomorrow's meeting using its agenda and related material.
- Where is the latest specification, and what discussion explains the change?
- What follow-ups were mentioned, and which have explicit owners?

Calendar questions require Calendar data. An invitation does not establish attendance;
a meeting summary does not independently corroborate its transcript.

## Optional graph enrichment

Antfly's graph index stores relationships; GLiNER2 proposes entities and relationships
from text; a validated projection connects the two. These are separate capabilities.
A general graph can relate people, projects, documents, messages, meetings and events.
No decision-specific ontology is required.

Search can power the agent before graph extraction works. Enable graph enrichment after
model inference, source-backed edges, traversal and permissions pass their own checks.
An advertised or connected model is not evidence of successful inference.

## Current implementation status

Experimental. The separate Antfly pilot has ingested selected Gmail, Drive and Meet snapshots
and exercised an agent over them. Calendar and continuous synchronization are not implemented.
The existing UI remains a specialized prototype, and its retrieval adapter currently calls
the Antfly API directly; it does not yet validate this Guide's complete MCP path.

Native graph indexing/traversal passed an isolated synthetic test. The latest GLiNER2
shared-model check returned HTTP 500, `MODEL_LOAD_FAILED` / `CudaUnavailable`.
Model-based graph enrichment is therefore unavailable, not a completed feature.

The reusable package contains no private source data or credentials. Customer-specific
integrations and internal product names belong in implementation notes, not this pattern.
