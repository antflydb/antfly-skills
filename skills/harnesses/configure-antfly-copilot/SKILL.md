---
name: configure-antfly-copilot
description: Configure, review, and smoke-test Microsoft Copilot Studio or GitHub Copilot connections to hosted Antfly Cloud MCP. Use when creating Copilot MCP configuration, setting the Cloud endpoint and bearer key, checking tool visibility, diagnosing Copilot MCP auth or path problems, or publishing a read-only Antfly-backed Copilot.
---

# Configure Antfly for Copilot

Determine whether the target is GitHub Copilot in VS Code or Microsoft Copilot
Studio before changing configuration.

## GitHub Copilot workflow

1. Collect the instance ID and intended key tier.
2. Use `https://platform.antfly.io/cloud/v1/<instance_id>/mcp/v1`.
3. Create `.vscode/mcp.json` from `references/github-copilot.md` using a placeholder.
4. Put the real key in a local/user secret mechanism; never commit it.
5. Ask Copilot to list Antfly tools and tables.
6. Fail a read-only verification if any mutation, backup, or restore tool is visible.

## Copilot Studio workflow

1. Create the remote MCP tool connection in the intended Power Platform environment.
2. Store the Bearer credential in the managed connection.
3. Disable “allow all tools” and select only read tools.
4. Test with both the editor identity and the published-agent identity.
5. Complete publication, sharing, channel, and administrator approval separately.

Diagnose endpoint path, `Bearer ` prefix, instance/key match, key tier and table
grants, then client-specific MCP support—in that order.
