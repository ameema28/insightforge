"""
Tests for InsightForge MCP Server.

Verifies that the MCP server correctly exposes data analysis tools
and that tool functions behave identically to direct agent tool calls.
"""
import os
import tempfile
import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.server import analyze_csv_tool, generate_chart_tool


class TestMCPServerTools:
    """Test MCP server tool functions directly."""

    def test_analyze_csv_tool_valid_file(self):
        """MCP analyze_csv_tool should return a valid data report."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            tmp.write("Product,Revenue,Units\n")
            tmp.write("Laptop,1200,2\n")
            tmp.write("Mouse,25,5\n")
            tmp.write("Keyboard,75,3\n")
            path = tmp.name

        try:
            result = analyze_csv_tool(file_path=path)
            assert "DATA SCOUT REPORT" in result
            assert "Rows: 3" in result
            assert "Product" in result
            assert "Revenue" in result
            assert "SECURITY_ERROR" not in result
            assert "PROCESSING_ERROR" not in result
        finally:
            os.unlink(path)

    def test_analyze_csv_tool_security_rejection(self):
        """MCP analyze_csv_tool should reject non-data files."""
        result = analyze_csv_tool(file_path="/tmp/malicious.exe")
        assert result.startswith("SECURITY_ERROR")

    def test_analyze_csv_tool_missing_file(self):
        """MCP analyze_csv_tool should handle missing files gracefully."""
        result = analyze_csv_tool(file_path="/nonexistent/path/data.csv")
        assert "SECURITY_ERROR" in result or "PROCESSING_ERROR" in result

    def test_generate_chart_tool_valid(self):
        """MCP generate_chart_tool should create a PNG file."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            tmp.write("Month,Sales\n")
            tmp.write("Jan,100\n")
            tmp.write("Feb,150\n")
            tmp.write("Mar,120\n")
            path = tmp.name

        try:
            result = generate_chart_tool(
                file_path=path,
                x_column="Month",
                y_column="Sales",
                chart_type="bar"
            )
            assert "saved successfully" in result
            png_path = result.split(": ")[-1]
            assert os.path.exists(png_path)
            os.unlink(png_path)
        finally:
            os.unlink(path)

    def test_generate_chart_tool_bad_column(self):
        """MCP generate_chart_tool should report missing columns."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            tmp.write("A,B\n1,2\n")
            path = tmp.name

        try:
            result = generate_chart_tool(
                file_path=path,
                x_column="NonExistent",
                y_column="B",
                chart_type="bar"
            )
            assert "ERROR" in result
            assert "not found" in result
        finally:
            os.unlink(path)

    def test_generate_chart_tool_invalid_type(self):
        """MCP generate_chart_tool should reject unsupported chart types."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            tmp.write("A,B\n1,2\n")
            path = tmp.name

        try:
            result = generate_chart_tool(
                file_path=path,
                x_column="A",
                y_column="B",
                chart_type="pie"
            )
            assert "ERROR" in result
            assert "Unsupported" in result
        finally:
            os.unlink(path)
