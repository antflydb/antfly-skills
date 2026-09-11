# Google runtime and Antfly MCP

## Google configuration

Discover the selected project, Vertex model and supported location; do not copy a demo's
project or model name into a customer's configuration. The earlier Python builds used ADK
1.39.1 with a dependency lock. Check compatibility before choosing another version.

For local Vertex access, inspect ADC without printing tokens. If absent, use Google's ADC
login flow for the intended account. `gcloud auth login` and
`gcloud auth application-default login` configure different consumers. Enable Vertex AI
and verify a model request with the intended identity/project. Reuse existing credentials
within the user's authorization. [ADC setup](https://docs.cloud.google.com/docs/authentication/provide-credentials-adc).

Configure these non-secret settings in the application environment:

| Setting | Purpose |
| --- | --- |
| `GOOGLE_GENAI_USE_VERTEXAI=TRUE` | Select Vertex AI in the Google client |
| `GOOGLE_CLOUD_PROJECT` | Selected billing/resource project |
| `GOOGLE_CLOUD_LOCATION` | Supported location for the selected model |
| `GOOGLE_MODEL` | Model available to that project; read explicitly in agent construction |
| `ANTFLY_MCP_URL` | Exact discovered endpoint |
| `ANTFLY_TABLE` | Table fixed by trusted application configuration |

Keep the read-only Antfly credential in a local ignored environment file or secret store.
Workspace OAuth and any other source credentials remain separate from Google runtime ADC.

## Choose the MCP integration shape

Prefer a bounded ADK function tool wrapping the MCP client when table filters, response
normalization or source-access checks must be enforced. The earlier incident agent used
this shape: `search_evidence` built a structured query and called Antfly's `query` tool
through a Streamable HTTP MCP session. It did not expose arbitrary query DSL to the model.

Within the trusted adapter, the tested Python SDK connection shape was:

```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def query_antfly(url, readonly_key, arguments):
    # arguments are built by trusted code from fixed table/scope, not arbitrary model DSL.
    async with streamablehttp_client(
        url, headers={"Authorization": "Bearer " + readonly_key}, sse_read_timeout=60
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("query", arguments)
            if result.isError:
                raise RuntimeError("Antfly retrieval failed")
            return result  # normalize and enforce source access before returning to the agent
```

The adapter needs result parsing and authorization in addition to this transport fragment.
Prefer `structuredContent` when supplied; otherwise parse the documented text JSON response.
Discover response envelopes, field names and tool schemas on the target. For the Antfly
query contract, `tableName` and `queryRequest` are separate arguments. `get_document`
requires its own discovered argument mapping and the same source-access boundary.

When the endpoint already enforces the required caller/source scope, ADK's `McpToolset`
with `StreamableHTTPConnectionParams` is another option. Select only the discovered retrieval
tools. A raw instance-wide toolset is not a private multi-user permission implementation.
Check the installed SDK against [ADK MCP guidance](https://google.github.io/adk-docs/tools-custom/mcp-tools/).

## Agent loop

Construct an ADK `Agent` using the selected model, grounding instructions and bounded search
tool. Use a runner and per-user/session isolation. An in-memory session service is suitable
for ephemeral demos; it is not durable, multi-instance chat storage.

Limit model/tool calls, passage count, output tokens and total duration. Choose generation
settings supported by the selected model; do not copy thinking parameters across models
without a test. Inspect final/finish/error events so a partial response is not shown as complete.
Stream observable retrieval progress and evidence, not hidden reasoning.

Validate citation IDs against returned evidence, verify source versions and test whether
passages actually support the claims. Citation existence is not an entailment guarantee.
Stop on auth failures; reconnect a transient transport once outside the model loop if suitable.
Redact nested transport exceptions that may contain headers or private content.

## Evidence from earlier builds

The synthetic incident application implemented ADK/Vertex reasoning over an actual Antfly
MCP client, with application-built filters and result normalization. The later Workspace
preview implemented Google runtime and private Cloud Run/IAP verification but used a direct
Antfly API adapter. Reuse each tested component honestly; the latter is not a Workspace MCP
verification result. No live deployment is created by reading or validating this Skill.
