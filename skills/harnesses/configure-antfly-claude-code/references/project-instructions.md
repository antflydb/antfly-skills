# CLAUDE.md fragment

- Retrieve required product evidence through Antfly MCP before answering.
- Use only `query` and `get_document` in normal operation.
- Prefer compact, direct chunk content; do not hydrate unnecessary ancestors or metadata.
- Make one intent-selected query and at most one focused fallback.
- Do not use shell, web, or filesystem tools as an undocumented retrieval fallback.
- Do not expose private storage paths, credentials, or retrieval diagnostics.
- Stop on authentication, authorization, invalid-request, and MCP tool errors.
