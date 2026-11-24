---
name: configure-antfly-claude-code
description: Configure, review, and smoke-test a Claude Code project connection to Antfly MCP, either Antfly Cloud or a self-hosted/local Antfly server. Use when registering Antfly MCP with Claude Code, applying a read-only tool allowlist, adding durable CLAUDE.md retrieval instructions, using the antfly CLI from Claude Code, or diagnosing Claude Code MCP authentication and connection issues.
---

# Configure Antfly for Claude Code

## Workflow

1. Export the exact `ANTFLY_MCP_URL` and a dedicated `ANTFLY_API_KEY` locally. Cloud uses
   `https://platform.antfly.io/cloud/v1/<instance_id>/mcp/v1`; a local server uses
   `http://127.0.0.1:8080/mcp/v1` (no trailing slash). Create a self-hosted key with
   `connect-antfly-mcp`.
2. Run `scripts/setup-mcp.sh` to create a machine-local registration. It requires HTTPS
   except for loopback hosts (`localhost`, `127.0.0.1`, `[::1]`).
3. To share the server with a team, `claude mcp add --scope project` writes `.mcp.json` at
   the project root instead. Never commit a key literal there; reference an environment
   variable such as `${ANTFLY_API_KEY}` in the header.
4. Add the rules in `references/project-instructions.md` to `CLAUDE.md` without adding secrets.
5. Start Claude Code, run `/mcp`, and verify the Antfly connection.
6. List available tools and ensure a read-only key cannot see write/admin operations.
7. Query a known table and verify explanatory evidence fits the tool-result budget
   (96 KiB by default; project focused `fields`, never `_chunks.*`).

Let Claude own the MCP session. Permit one focused retrieval fallback, but do
not allow shell or filesystem search to substitute for required Antfly evidence.

## antfly CLI agent mode

When Claude Code runs the `antfly` CLI with stdout piped, `CLAUDECODE` selects agent
mode automatically (force with `antfly --agent ...`, disable with `--no-agent`). Use
`antfly --agent capabilities`, `schema`, `query`, `sql`, and `lookup` for a versioned
output contract. The CLI reads `ANTFLY_URL` (server base URL) and `ANTFLY_TOKEN`
(encoded API key); keep both out of committed files.
