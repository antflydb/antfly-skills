---
name: configure-antfly-n8n
description: Build and verify an n8n AI Agent workflow using Antfly Cloud MCP as its retrieval layer. Use when adding an MCP Client Tool node, configuring Antfly credentials in n8n, limiting available tools, grounding workflow answers, or connecting retrieval to tickets, CRM, email, and other n8n actions.
---

# Configure Antfly for n8n

## Workflow

1. Create a dedicated read-only Antfly key in the intended environment.
2. Store it in an n8n credential; do not put it directly in workflow JSON.
3. Add an MCP Client Tool node using the exact Antfly Cloud MCP endpoint.
4. Disable automatic exposure of all tools. Select `query` and `get_document`.
5. Apply `assets/system-message.md` to the AI Agent node and replace placeholders.
6. Keep business-action credentials and nodes separate from Antfly retrieval.
7. Test broad, exact, unsupported, unrelated, and connection-failure cases.
8. Verify the workflow stops after a connection failure rather than retrying through the model.

n8n owns orchestration; Antfly owns evidence retrieval. Do not place sending,
publishing, CRM updates, or ticket changes inside the Antfly credential boundary.
