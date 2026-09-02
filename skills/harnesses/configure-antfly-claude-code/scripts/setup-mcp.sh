#!/usr/bin/env bash
set -euo pipefail

command -v claude >/dev/null 2>&1 || { echo "Claude Code is not on PATH." >&2; exit 1; }
: "${ANTFLY_MCP_URL:?ANTFLY_MCP_URL is required}"
: "${ANTFLY_API_KEY:?ANTFLY_API_KEY is required}"

case "${ANTFLY_MCP_URL}" in https://*) ;; *) echo "Remote MCP URL must use HTTPS." >&2; exit 1 ;; esac

claude mcp remove antfly --scope local >/dev/null 2>&1 || true
claude mcp add --transport http --scope local antfly "${ANTFLY_MCP_URL}" --header "Authorization: Bearer ${ANTFLY_API_KEY}"
echo "Registered Antfly MCP locally. Run /mcp in Claude Code to verify it."
