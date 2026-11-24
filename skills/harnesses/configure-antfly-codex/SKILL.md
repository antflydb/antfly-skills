---
name: configure-antfly-codex
description: Configure, review, and smoke-test a Codex project connection to Antfly MCP, either Antfly Cloud or a self-hosted/local Antfly server. Use when registering Antfly MCP with Codex, storing an Antfly bearer-token environment variable, restricting tools to read-only retrieval, using the antfly CLI from Codex, or adding durable Antfly instructions to a repository.
---

# Configure Antfly for Codex

## Workflow

1. Require `ANTFLY_MCP_URL` and `ANTFLY_API_KEY` in the launching shell. Cloud uses
   `https://platform.antfly.io/cloud/v1/<instance_id>/mcp/v1`; a local server uses
   `http://127.0.0.1:8080/mcp/v1`.
2. Confirm the key is scoped to the intended instance or tables and read-only for retrieval
   use cases (create self-hosted keys with `connect-antfly-mcp`).
3. Run `scripts/setup-mcp.sh`; it stores only the environment-variable name in Codex
   configuration and requires HTTPS except for loopback hosts.
4. Add durable repository instructions from `references/project-instructions.md` to the applicable `AGENTS.md`.
5. Restart or relaunch Codex from a shell that still exports the key.
6. Ask Codex to list capabilities and tables, then query a known table.
7. Verify mutation tools are not available to a read-only key.

Never write the plaintext key into `AGENTS.md`, MCP configuration, command output, or source control.

## antfly CLI agent mode

When Codex runs the `antfly` CLI with stdout piped, `CODEX_THREAD_ID` selects agent mode
automatically (force with `antfly --agent ...`, disable with `--no-agent`). Use
`antfly --agent capabilities`, `schema`, `query`, `sql`, and `lookup` for a versioned
output contract. The CLI reads `ANTFLY_URL` (server base URL) and `ANTFLY_TOKEN`
(encoded API key).
