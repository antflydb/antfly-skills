---
name: configure-antfly-claude-code
description: Configure, review, and smoke-test a Claude Code project connection to hosted Antfly Cloud MCP. Use when registering Antfly MCP with Claude Code, applying a read-only tool allowlist, adding durable CLAUDE.md retrieval instructions, or diagnosing Claude Code MCP authentication and connection issues.
---

# Configure Antfly for Claude Code

## Workflow

1. Export the exact `ANTFLY_MCP_URL` and a dedicated `ANTFLY_API_KEY` locally.
2. Run `scripts/setup-mcp.sh` to create a machine-local registration.
3. Add the rules in `references/project-instructions.md` to `CLAUDE.md` without adding secrets.
4. Start Claude Code, run `/mcp`, and verify the Antfly connection.
5. List available tools and ensure a read-only key cannot see write/admin operations.
6. Query a known table and verify explanatory evidence fits the tool-result budget.

Let Claude own the MCP session. Permit one focused retrieval fallback, but do
not allow shell or filesystem search to substitute for required Antfly evidence.
