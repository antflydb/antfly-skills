---
name: configure-antfly-n8n
description: Build and verify an n8n AI Agent workflow using Antfly MCP (Antfly Cloud or self-hosted) as its retrieval layer. Use when adding an MCP Client Tool node, configuring Antfly credentials in n8n, limiting available tools, grounding workflow answers, or connecting retrieval to tickets, CRM, email, and other n8n actions.
---

# Configure Antfly for n8n

## Workflow

1. Create a dedicated read-only Antfly key in the intended environment (Cloud: an instance key of type read only; self-hosted: see `connect-antfly-mcp`).
2. Store it in an n8n credential; do not put it directly in workflow JSON.
3. Add an MCP Client Tool node using the exact MCP endpoint (Cloud: `https://platform.antfly.io/cloud/v1/<instance_id>/mcp/v1`), with Bearer Auth holding the token only.
4. Disable automatic exposure of all tools. Select `query` and `get_document`, then run the
   MCP node alone; it should list exactly those two tools.
5. Apply `assets/system-message.md` to the AI Agent node and replace placeholders. It pins the
   tool input to exactly two outer properties, `tableName` and `queryRequest`, with
   `queryRequest` an object (never a string) and `"hierarchy": {}` for chunk-level hits.
   An `invalid query request` error almost always means `queryRequest` arrived as a quoted
   string or mixed with shorthand arguments; inspect the failed tool call's input.
6. Set chat-model temperature to 0–0.1 and agent maximum iterations to 4–6.
7. Keep business-action credentials and nodes separate from Antfly retrieval.
8. Test broad, exact, unsupported, unrelated, and connection-failure cases.
9. Verify the workflow stops after a connection failure rather than retrying through the model.

n8n owns orchestration; Antfly owns evidence retrieval. Do not place sending,
publishing, CRM updates, or ticket changes inside the Antfly credential boundary.
