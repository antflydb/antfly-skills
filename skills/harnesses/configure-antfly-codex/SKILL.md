---
name: configure-antfly-codex
description: Configure, review, and smoke-test a Codex project connection to hosted Antfly Cloud MCP. Use when registering Antfly MCP with Codex, storing an Antfly bearer-token environment variable, restricting tools to read-only retrieval, or adding durable Antfly instructions to a repository.
---

# Configure Antfly for Codex

## Workflow

1. Require `ANTFLY_MCP_URL` and `ANTFLY_API_KEY` in the launching shell.
2. Confirm the key is instance-scoped and read-only for retrieval use cases.
3. Run `scripts/setup-mcp.sh`; it stores only the environment-variable name in Codex configuration.
4. Add durable repository instructions from `references/project-instructions.md` to the applicable `AGENTS.md`.
5. Restart or relaunch Codex from a shell that still exports the key.
6. Ask Codex to list capabilities and tables, then query a known table.
7. Verify mutation tools are not available to a read-only key.

Never write the plaintext key into `AGENTS.md`, MCP configuration, command output, or source control.
