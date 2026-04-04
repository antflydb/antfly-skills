# A2A Protocol — Agent-to-Agent

## What It Is

Antfly implements Google's Agent-to-Agent (A2A) protocol, enabling AI agents to communicate with Antfly as a peer agent — not just a database. This is higher-level than MCP: where MCP provides tools for CRUD operations, A2A provides skills for complex multi-step reasoning.

**Endpoints**:
- JSON-RPC: `{{ANTFLY_API_URL}}/a2a`
- Agent Card (discovery): `{{ANTFLY_API_URL}}/.well-known/agent.json`

Starts automatically with the metadata server.

## Agent Card

`GET /.well-known/agent.json` returns:

```json
{
  "name": "Antfly",
  "skills": ["retrieval", "query-builder"],
  "capabilities": {
    "streaming": true,
    "stateHistory": true
  },
  "defaultModes": ["text", "data"]
}
```

Any A2A-compatible agent can discover Antfly's capabilities automatically.

## Skills

### `retrieval` — RAG Agent

The retrieval skill runs multi-strategy search and optionally generates LLM-powered answers with streaming.

**Two modes**:
- **Pipeline** (non-agentic) — single-pass retrieval + generation
- **Agentic** — LLM-powered loop with multi-turn conversation, clarification questions, and iterative refinement

**Input**: Text query + optional config (table name, max iterations)

**Output** (streamed as A2A artifact updates):
- Retrieved document hits
- Generated answer text
- Clarification questions (when more info needed)
- Follow-up suggestions

**Features**:
- Multi-turn conversation — extracts chat history from stored task state
- Streaming — real-time artifact updates as retrieval and generation progress
- Terminal states: `Completed` or `InputRequired` (awaiting clarification)

### `query-builder` — Natural Language to Query

Translates natural language intent into structured Bleve search queries using an LLM.

**Input**: Text description of what to search for + optional table name and schema fields

**Output**:
- Structured Bleve query JSON
- Human-readable explanation of the query
- Confidence score
- Warnings (if any ambiguity)

**Example**: "Find articles about machine learning published after 2025 with more than 100 citations" → structured Bleve conjuncts query with match + date_range + numeric_range.

## When to Use MCP vs. A2A

| Need | Use |
|------|-----|
| Create/drop tables | MCP |
| Insert/delete documents | MCP |
| Simple queries | MCP |
| List/manage indexes | MCP |
| Backup/restore | MCP |
| RAG with streaming answers | **A2A** (retrieval skill) |
| Multi-turn conversational search | **A2A** (retrieval skill) |
| Natural language → search query | **A2A** (query-builder skill) |
| Complex reasoning over search results | **A2A** (agentic mode) |

In short: MCP for database operations, A2A for intelligent search and reasoning.

## Sharp Edges

1. **A2A is JSON-RPC**, not REST — requests go to `/a2a` as JSON-RPC calls, not individual REST endpoints
2. **Agent card at `/.well-known/agent.json`** — standard A2A discovery path
3. **Streaming uses A2A artifact updates**, not SSE — different from the REST retrieval agent endpoint
4. **Cancel operations are stubbed** — cancellation requests are accepted but don't interrupt in-flight operations yet
5. **Agentic mode requires an LLM** — the retrieval skill needs a configured generator (ollama, openai, etc.) for agentic mode; pipeline mode works without one
