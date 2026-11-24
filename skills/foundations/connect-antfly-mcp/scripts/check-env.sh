#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${ANTFLY_MCP_URL:-}" ]]; then
  echo "ANTFLY_MCP_URL is not set." >&2
  exit 1
fi

if [[ -z "${ANTFLY_API_KEY:-}" ]]; then
  echo "ANTFLY_API_KEY is not set." >&2
  exit 1
fi

case "${ANTFLY_MCP_URL}" in
  http://*@*) echo "Credentials in the MCP URL are not allowed." >&2; exit 1 ;;
  https://*|http://localhost:*|http://localhost/*|http://127.0.0.1:*|http://127.0.0.1/*|http://\[::1\]:*|http://\[::1\]/*) ;;
  *) echo "Use HTTPS for non-loopback MCP endpoints." >&2; exit 1 ;;
esac

echo "Antfly MCP environment is present. Credential value was not printed."
