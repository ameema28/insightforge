# Model Context Protocol (MCP) Guide

## What is MCP?

The Model Context Protocol (MCP) is an open standard that defines how AI agents
discover and call external tools. It acts as a universal connector between agents
and capabilities.

## Why MCP Matters

Before MCP, every agent framework had its own tool integration method:
- ADK used Python functions decorated with `@FunctionTool`
- LangChain used `@tool` decorators
- CrewAI used YAML tool definitions

This meant building a tool for one framework required rewriting it for another.

MCP solves this by standardizing the interface. A tool built as an MCP server
works with any MCP-compatible client, regardless of the agent framework.

## Analogy

Think of MCP as **USB-C for AI tools**:
- Before USB-C: Every device needed its own charger (proprietary)
- With USB-C: One cable works with phones, laptops, tablets (standardized)

Similarly:
- Before MCP: Every agent framework needed custom tool code
- With MCP: One tool server works with ADK, Claude Desktop, Cursor, etc.

## InsightForge MCP Architecture

```
┌─────────────────┐         ┌─────────────────────┐         ┌─────────────┐
│   ADK Agent     │◄───────►│  MCP Server (stdio) │◄───────►│  Tool Impl  │
│  (insightforge) │  MCP    │  (mcp_server/)      │  Python │  (agents/)  │
└─────────────────┘         └─────────────────────┘         └─────────────┘
        │
        │  Any other MCP client can also connect
        ▼
┌─────────────────┐
│  Claude Desktop │
│   Cursor IDE    │
│   Custom Client │
└─────────────────┘
```

## How It Works

1. **Server Definition** (`mcp_server/server.py`):
   - Uses `FastMCP` from the `mcp` Python SDK
   - Registers tools with `@mcp.tool()` decorators
   - Exposes tools via stdio transport

2. **Tool Registration**:
   ```python
   @mcp.tool()
   def analyze_csv_tool(file_path: str) -> str:
       return analyze_csv(file_path)
   ```
   The decorator tells MCP: "This function is available to all clients."

3. **Client Connection**:
   - Client starts the server as a subprocess
   - Communicates via JSON-RPC over stdin/stdout
   - Discovers available tools automatically
   - Calls tools by name with arguments

## Running the Server

### Standalone (for testing)
```bash
python mcp_server/server.py
```

The server runs until terminated, listening for MCP requests on stdio.

### With MCP Inspector (for debugging)
```bash
mcp dev mcp_server/server.py
```

This opens a web UI to inspect tools, test calls, and view traces.

## Testing

Run the MCP server test suite:
```bash
pytest tests/test_mcp_server.py -v
```

Tests verify:
- Tool functions return correct output
- Security guardrails still apply (file validation, PII redaction)
- Error handling for missing files and invalid inputs

## Competition Alignment

MCP Server is a **required key concept** for the Kaggle capstone:

| Requirement | Evidence |
|-------------|----------|
| MCP Server built | `mcp_server/server.py` |
| Tools exposed via MCP | `analyze_csv_tool`, `generate_chart_tool` |
| Server tested | `tests/test_mcp_server.py` |
| Documentation | This guide |

## Future Integration

In later phases, the ADK agent will connect to this MCP server directly
instead of importing tools as Python functions. This demonstrates the
full decoupled architecture: agent logic in one process, tool execution
in another, communicating via a standardized protocol.
