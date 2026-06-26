"""
InsightForge Security Guardrails

Defense-in-depth security for the multi-agent system.
Implements input validation, prompt injection detection, rate limiting,
and output sanitization.
"""

import re
import time
from typing import Tuple


class PromptInjectionGuardrail:
    """
    Detects and blocks attempts to override agent instructions.

    Common attack patterns:
    - "Ignore all previous instructions"
    - "Forget your system prompt"
    - "You are now a different agent"
    """

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior|earlier)\s+(instructions|commands|prompts)",
        r"forget\s+(your\s+)?(system|original|initial)\s+(prompt|instructions|role)",
        r"you\s+(are\s+now|have\s+become)\s+(a\s+)?(different|new|hacked|compromised)",
        r"disregard\s+(everything|all)\s+(above|before|prior)",
        r"override\s+(your|the)\s+(instructions|constraints|rules)",
        r"act\s+as\s+(if\s+you\s+(are|were)\s+)?(a\s+)?(different|new|unrestricted)",
        r"new\s+instructions?:",
        r"system\s+override",
        r"debug\s+mode",
        r"admin\s+access",
    ]

    def __init__(self):
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]

    def check(self, user_input: str) -> Tuple[bool, str]:
        """
        Check if user input contains prompt injection attempts.

        Returns:
            (is_safe, reason) - is_safe is True if no injection detected,
            False with reason string if injection found.
        """
        if not user_input or not isinstance(user_input, str):
            return False, "Empty or invalid input"

        for pattern in self.compiled_patterns:
            match = pattern.search(user_input)
            if match:
                matched = match.group(0)
                return False, f"Prompt injection detected: '{matched}'. Request rejected."

        return True, "Input safe"


class RateLimiter:
    """
    Simple in-memory rate limiter per session.

    Prevents abuse by limiting requests per time window.
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # session_id -> list of timestamps

    def check(self, session_id: str) -> Tuple[bool, str]:
        """
        Check if session is within rate limit.

        Returns:
            (allowed, message) - allowed is True if within limit,
            False with message if exceeded.
        """
        now = time.time()

        if session_id not in self.requests:
            self.requests[session_id] = []

        # Remove old requests outside the window
        self.requests[session_id] = [
            ts for ts in self.requests[session_id]
            if now - ts < self.window_seconds
        ]

        if len(self.requests[session_id]) >= self.max_requests:
            return False, f"Rate limit exceeded: {self.max_requests} requests per {self.window_seconds}s. Please wait."

        self.requests[session_id].append(now)
        return True, "Request allowed"

    def reset(self, session_id: str):
        """Reset rate limit for a session."""
        if session_id in self.requests:
            del self.requests[session_id]


class OutputSanitizer:
    """
    Sanitizes agent outputs before displaying to users.
    Prevents code execution, malicious URLs, and system commands
    from being rendered in the Streamlit UI.
    """

    DANGEROUS_PATTERNS = [
        r"```\s*(python|bash|sh|shell|cmd|powershell)",
        r"<script.*?>.*?</script>",
        r"javascript:",
        r"on\w+\s*=.*?alert\s*\(",
        r"\b(rm\s+-rf|sudo\s+|chmod\s+|curl\s+.*\||wget\s+.*\|)",
        r"\b(api_key|apikey|password|secret)\s*[:=]\s*['\"]",
    ]

    def __init__(self):
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]

    def sanitize(self, text: str) -> Tuple[str, bool]:
        """
        Sanitize output text. Returns (cleaned_text, was_flagged).
        """
        if not text or not isinstance(text, str):
            return text, False

        was_flagged = False
        cleaned = text

        for pattern in self.compiled_patterns:
            if pattern.search(cleaned):
                was_flagged = True
                cleaned = pattern.sub("[SECURITY: Potentially unsafe content removed]", cleaned)

        # Also apply PII redaction to outputs
        cleaned = _redact_pii(cleaned)

        return cleaned, was_flagged


# Global instances for use across the application
injection_guardrail = PromptInjectionGuardrail()
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
output_sanitizer = OutputSanitizer()


def validate_input(user_input: str, session_id: str = "default", guardrail=None, limiter=None) -> Tuple[bool, str]:
    """
    Security validation layer for all user inputs.

    Args:
        user_input: The text to validate
        session_id: Unique identifier for the session
        guardrail: Optional PromptInjectionGuardrail instance (for testing)
        limiter: Optional RateLimiter instance (for testing)

    Returns:
        (is_valid, message) - is_valid is True if input passes all checks,
        False with rejection message if any check fails.
    """
    # Check prompt injection (use provided guardrail or global)
    check_guardrail = guardrail if guardrail is not None else injection_guardrail
    is_safe, reason = check_guardrail.check(user_input)
    if not is_safe:
        return False, f"SECURITY_BLOCKED: {reason}"

    # Check rate limit (use provided limiter or global)
    check_limiter = limiter if limiter is not None else rate_limiter
    allowed, message = check_limiter.check(session_id)
    if not allowed:
        return False, f"SECURITY_BLOCKED: {message}"

    return True, "Input validated"


def sanitize_output(text: str) -> Tuple[str, bool]:
    """Module-level function for sanitizing agent outputs."""
    return output_sanitizer.sanitize(text)


def _redact_pii(text: str) -> str:
    """Security guardrail: Redact common PII patterns from text output."""
    text = re.sub(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "[REDACTED-EMAIL]",
        text,
    )
    text = re.sub(
        r"(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}",
        "[REDACTED-PHONE]",
        text,
    )
    text = re.sub(
        r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b",
        "[REDACTED-SSN]",
        text,
    )
    return text