#!/usr/bin/env bash
set -euo pipefail

command -v codex >/dev/null 2>&1 || { echo "Codex CLI is not on PATH." >&2; exit 1; }
: "${ANTFLY_MCP_URL:?ANTFLY_MCP_URL is required}"
: "${ANTFLY_API_KEY:?ANTFLY_API_KEY is required in this shell}"

case "${ANTFLY_MCP_URL}" in https://*) ;; *) echo "Remote MCP URL must use HTTPS." >&2; exit 1 ;; esac

codex mcp remove antfly >/dev/null 2>&1 || true
codex mcp add antfly --url "${ANTFLY_MCP_URL}" --bearer-token-env-var ANTFLY_API_KEY
echo "Registered Antfly MCP. Relaunch Codex from a shell that exports ANTFLY_API_KEY."
