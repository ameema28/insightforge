"""
Day 1 Test Suite for InsightForge

Run with:
    pytest tests/test_day1.py -v
Or:
    pytest
"""
import os
import tempfile
import pytest

from agents.tools import analyze_csv, generate_chart, _validate_file_path, _redact_pii
from agents.agent import root_agent


class TestSecurityGuardrails:
    """Security is a key competition concept. These tests verify our guardrails."""

    def test_validate_missing_file(self):
        """Agent should reject non-existent files."""
        valid, msg = _validate_file_path("/fake/path/data.csv")
        assert not valid
        assert "not found" in msg.lower()

    def test_validate_bad_extension(self):
        """Agent should reject non-data files (security)."""
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as tmp:
            tmp.write(b"malicious")
            path = tmp.name
        try:
            valid, msg = _validate_file_path(path)
            assert not valid
            assert "invalid file type" in msg.lower()
        finally:
            os.unlink(path)

    def test_pii_redaction_email(self):
        """PII should be redacted from outputs."""
        text = "Contact us at admin@company.com or support@org.net"
        result = _redact_pii(text)
        assert "admin@company.com" not in result
        assert "[REDACTED-EMAIL]" in result

    def test_pii_redaction_phone(self):
        """Phone numbers should be redacted."""
        text = "Call me at 555-123-4567 or (555) 987-6543"
        result = _redact_pii(text)
        assert "555-123-4567" not in result
        assert "[REDACTED-PHONE]" in result


class TestDataTools:
    """Tests for core data analysis functionality."""

    def test_analyze_csv_success(self):
        """Tool should correctly analyze a valid CSV."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            tmp.write("Product,Revenue,Units\n")
            tmp.write("Laptop,1200,2\n")
            tmp.write("Mouse,25,5\n")
            tmp.write("Keyboard,75,3\n")
            path = tmp.name
        try:
            result = analyze_csv(path)
            assert "DATA SCOUT REPORT" in result
            assert "Rows: 3" in result
            assert "Product" in result
            assert "Revenue" in result
            assert "SECURITY_ERROR" not in result
            assert "PROCESSING_ERROR" not in result
        finally:
            os.unlink(path)

    def test_analyze_csv_with_missing_values(self):
        """Tool should flag missing values as data quality issues."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            tmp.write("A,B,C\n")
            tmp.write("1,,3\n")
            tmp.write("2,2,\n")
            path = tmp.name
        try:
            result = analyze_csv(path)
            assert "Missing Values" in result
            assert "ALERT" in result or "missing values detected" in result.lower()
        finally:
            os.unlink(path)

    def test_analyze_csv_security_error(self):
        """Tool should return SECURITY_ERROR for invalid input."""
        result = analyze_csv("/tmp/malicious.exe")
        assert result.startswith("SECURITY_ERROR")

    def test_generate_chart_success(self):
        """Chart generation should produce a PNG file."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            tmp.write("Month,Sales\n")
            tmp.write("Jan,100\n")
            tmp.write("Feb,150\n")
            tmp.write("Mar,120\n")
            path = tmp.name
        try:
            result = generate_chart(path, "Month", "Sales", "bar")
            assert "saved successfully" in result
            png_path = result.split(": ")[-1]
            assert os.path.exists(png_path)
            os.unlink(png_path)
        finally:
            os.unlink(path)

    def test_generate_chart_bad_column(self):
        """Chart tool should handle missing columns gracefully."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            tmp.write("A,B\n1,2\n")
            path = tmp.name
        try:
            result = generate_chart(path, "NonExistent", "B", "bar")
            assert "ERROR" in result
            assert "not found" in result
        finally:
            os.unlink(path)


class TestAgentInitialization:
    """Tests verifying ADK agent setup."""

    def test_agent_name(self):
        """Agent should have correct name for competition tracking."""
        assert root_agent.name == "insightforge_v1"

    def test_agent_model(self):
        """Agent should use Gemini 2.5 Flash."""
        assert root_agent.model == "gemini-2.5-flash"

    def test_agent_has_tools(self):
        """Agent must have data tools attached."""
        assert len(root_agent.tools) >= 2

    def test_agent_instruction_exists(self):
        """Agent should have detailed system instructions."""
        assert root_agent.instruction is not None
        assert len(root_agent.instruction) > 100
        assert "SECURITY" in root_agent.instruction
