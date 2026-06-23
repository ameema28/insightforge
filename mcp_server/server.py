"""
InsightForge MCP Server

Exposes data analysis tools via the Model Context Protocol (MCP).
Any MCP-compatible client can connect to this server and use its tools,
regardless of the underlying agent framework (ADK, LangChain, CrewAI, etc.).

Run with:
    python mcp_server/server.py

The server uses stdio transport, making it compatible with MCP clients
that communicate via standard input/output streams.
"""
import sys
from pathlib import Path

# Ensure project root is in Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp.server.fastmcp import FastMCP
from agents.tools import analyze_csv, generate_chart

# Create MCP server instance with descriptive name
mcp = FastMCP("insightforge-mcp")


@mcp.tool()
def analyze_csv_tool(file_path: str) -> str:
    """
    Analyze a CSV or Excel file and return structured summary statistics.

    Performs data scouting: row counts, column names, data types,
    missing value detection, and basic numeric statistics.

    Args:
        file_path: Absolute or relative path to the CSV or Excel file.

    Returns:
        Formatted report with file metadata, data quality flags,
        and numeric summary. Returns SECURITY_ERROR if validation fails.
    """
    return analyze_csv(file_path)


@mcp.tool()
def generate_chart_tool(
    file_path: str,
    x_column: str,
    y_column: str,
    chart_type: str = "bar"
) -> str:
    """
    Generate a chart from a CSV or Excel file and save as PNG.

    Args:
        file_path: Path to the data file.
        x_column: Column name for the X-axis.
        y_column: Column name for the Y-axis.
        chart_type: Type of chart. Must be one of: bar, line, scatter.

    Returns:
        Confirmation message with the absolute path to the saved PNG file.
        Returns ERROR if columns are not found or chart type is invalid.
    """
    return generate_chart(file_path, x_column, y_column, chart_type)


if __name__ == "__main__":
    # Run with stdio transport for MCP client connections
    mcp.run(transport="stdio")
