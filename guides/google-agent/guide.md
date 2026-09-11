# Build a Google Agent with Antfly

Use **Google ADK + Gemini on Vertex AI + Antfly MCP** to build a grounded agent over
your indexed data. Deploy privately on Cloud Run when a hosted experience is needed.

Google supplies the agent runtime and model. Antfly supplies the evidence and retrieval.
The data can come from Workspace, BigQuery, GitHub, documents or another supported ingestion
path. This Guide starts with a searchable Antfly dataset; it does not imply those connectors
are all bundled or connected.

## What you need

- A Google Cloud project, an available Vertex model, and an authorized runtime identity.
- A searchable Antfly table, its MCP endpoint and a dedicated read-only credential.
- The intended source-access policy and a small set of questions with known evidence.

## Build path

1. **Prepare the data.** Use the appropriate ingestion workflow and verify Antfly search.
2. **Set up Google.** Configure ADK, local application-default credentials and Vertex settings.
3. **Connect Antfly MCP.** Discover tool schemas and verify query and source lookup.
4. **Build the agent.** Add a bounded retrieval tool, citations, session isolation and failure
   handling. Enforce private source scope outside the model.
5. **Test the workflow.** Run supported, unsupported and access-failure cases through the agent.
6. **Host if needed.** Deploy code and protected configuration to Cloud Run; verify private
   access, authenticated answers and citations on the deployed service.

Follow [configure-antfly-google-adk](../../skills/harnesses/configure-antfly-google-adk/SKILL.md)
for runtime setup, MCP integration, grounding instructions and Cloud Run checks.

## How the Guides fit together

The [Workspace Agent Guide](../workspace-agent/guide.md) covers connecting and ingesting
Workspace sources and working across that dataset. Choose this Google runtime Skill when
ADK is the desired agent. Another runtime can use the same Workspace dataset, and this
Google runtime can use a different Antfly dataset.

Neither a decision-specific workflow nor an internal Antfly application is required.
Graph enrichment is optional and depends on separately verified Antfly inference/indexes.

## Package status

Experimental reusable package based on earlier Google-stack implementations. The synthetic
incident app used a real Antfly MCP adapter; the private Workspace prototype exercised
ADK/Vertex and Cloud Run/IAP with a direct API adapter. The Guide preserves those distinctions.
Library validation checks packaging, not a new customer's live deployment. Run the bundled
acceptance checks against the actual selected app and dataset before calling it verified.
