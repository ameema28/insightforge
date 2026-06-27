"""
ADK Runner Bridge for Streamlit

Provides a synchronous interface over the async ADK Runner.
Includes Groq fallback for when Gemini API is rate-limited.
Implements caching, retry logic, and intelligent chart detection.
"""
import asyncio
import inspect
import re
import os
import hashlib
from pathlib import Path
from typing import Optional, Tuple

# Load .env before any other imports that need it
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=str(env_path))
else:
    load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.orchestrator import root_agent
from agents.tools import generate_chart


# Conditional Groq import with safe fallback
Groq = None  # type: ignore
GROQ_AVAILABLE = False
try:
    from groq import Groq as _GroqClient  # type: ignore
    Groq = _GroqClient
    GROQ_AVAILABLE = True
except ImportError:
    pass


class GroqFallback:
    """Fallback LLM client using Groq API."""

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or "your" in api_key.lower() or len(api_key) < 20:
            raise ValueError(
                "GROQ_API_KEY is missing or appears to be a placeholder. "
                "Get a real key from console.groq.com"
            )

        if Groq is None:
            raise ImportError("Groq package is not installed. Run: pip install groq")

        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generate text response from Groq."""
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=4096,
            )
            content = response.choices[0].message.content
            return content if content is not None else ""
        except Exception as e:
            return f"Groq error: {str(e)}"


class InsightForgeRunner:
    """Synchronous wrapper around ADK Runner for Streamlit."""

    def __init__(self, session_id: str = "streamlit_user_001"):
        self.session_id = session_id
        self.user_id = "streamlit_user"
        self.app_name = "insightforge"
        self._session_service = InMemorySessionService()
        self._runner = Runner(
            agent=root_agent,
            app_name=self.app_name,
            session_service=self._session_service,
        )
        self._trace_log: list[str] = []
        self._cache: dict[str, str] = {}
        self._groq: Optional[GroqFallback] = None

        print(f"DEBUG Runner init: GROQ_API_KEY exists = {bool(os.getenv('GROQ_API_KEY'))}")
        print(f"DEBUG Runner init: GOOGLE_API_KEY exists = {bool(os.getenv('GOOGLE_API_KEY'))}")

        if GROQ_AVAILABLE and os.getenv("GROQ_API_KEY"):
            try:
                self._groq = GroqFallback()
                print("DEBUG Groq initialized successfully")
            except Exception as e:
                print(f"Groq init warning: {e}")
        else:
            print(f"DEBUG Groq not available: GROQ_AVAILABLE={GROQ_AVAILABLE}, key_exists={bool(os.getenv('GROQ_API_KEY'))}")

    async def _ensure_session(self) -> None:
        """Create ADK session if it does not already exist."""
        try:
            result = self._session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=self.session_id,
                state={},
            )
            if inspect.isawaitable(result):
                await result
        except Exception as e:
            error_str = str(e).lower()
            if "already exists" not in error_str and "duplicate" not in error_str:
                print(f"Warning: Session creation issue: {e}")

    def _is_chart_request(self, prompt: str) -> bool:
        """Detect if user is asking for a chart."""
        prompt_lower = prompt.lower()
        chart_keywords = [
            'chart', 'graph', 'plot', 'visualize', 'visualization',
            'bar chart', 'line chart', 'scatter plot', 'pie chart',
            'histogram', 'show me', 'plot of'
        ]
        return any(kw in prompt_lower for kw in chart_keywords)

    def _extract_file_path(self, prompt: str) -> Optional[str]:
        """Extract file path from prompt."""
        if '(File:' in prompt:
            return prompt.split('(File:')[1].split(')')[0].strip()
        return None

    def _detect_columns(self, df, prompt: str) -> Tuple[str, str]:
        """
        Intelligently detect x and y columns from prompt and dataframe.
        Falls back to first categorical and first numeric column.
        """
        prompt_lower = prompt.lower()
        cols = list(df.columns)

        mentioned = [c for c in cols if c.lower() in prompt_lower]

        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        num_cols = df.select_dtypes(include=['number']).columns.tolist()

        x_col = ""
        y_col = ""

        for c in mentioned:
            if c in cat_cols and not x_col:
                x_col = c
            elif c in num_cols and not y_col:
                y_col = c

        if not x_col and cat_cols:
            x_col = cat_cols[0]
        if not y_col and num_cols:
            y_col = num_cols[0]

        if not x_col:
            x_col = cols[0]
        if not y_col:
            y_col = cols[1] if len(cols) > 1 else cols[0]

        return x_col, y_col

    def _build_system_prompt(self) -> str:
        """Build system prompt for Groq fallback."""
        return """You are InsightForge, a professional data analyst assistant specializing in business intelligence.

YOUR CAPABILITIES:
1. Analyze CSV/Excel files and generate data quality reports.
2. Summarize findings in clear, business-friendly language.
3. Highlight data quality issues (missing values, outliers) as risks.

TONE:
- Professional, concise, and actionable.
- Use business language, not raw technical jargon.
- Highlight data quality issues as risks."""

    def _get_cache_key(self, prompt: str, file_path: Optional[str]) -> str:
        """Generate cache key from prompt and file."""
        key_data = f"{prompt}:{file_path or ''}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def generate_chart_direct(self, file_path: str, prompt: str) -> str:
        """Generate chart directly without LLM."""
        import pandas as pd

        try:
            if file_path.lower().endswith(".csv"):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
        except Exception as e:
            return f"Error loading file: {str(e)}"

        x_col, y_col = self._detect_columns(df, prompt)
        self._trace_log.append(f"[CHART] Detected columns: x={x_col}, y={y_col}")

        chart_type = 'bar'
        if any(kw in prompt.lower() for kw in ['line', 'trend', 'over time']):
            chart_type = 'line'
        elif any(kw in prompt.lower() for kw in ['scatter', 'correlation', 'vs']):
            chart_type = 'scatter'

        chart_result = generate_chart(file_path, x_col, y_col, chart_type)

        if chart_result and chart_result.startswith('data:image/png;base64,'):
            self._trace_log.append(f"[CHART] Success: {x_col} vs {y_col} ({chart_type})")
            return chart_result
        else:
            self._trace_log.append(f"[CHART] Failed: {chart_result}")
            return f"Error: Could not generate chart. {chart_result}"

    def run(self, prompt: str) -> str:
        """Execute multi-agent pipeline and return final text."""
        self._trace_log = []
        self._trace_log.append(f"[START] Received: {prompt[:80]}...")

        file_path = self._extract_file_path(prompt)

        # CHART REQUEST: Bypass LLM entirely, generate locally
        if self._is_chart_request(prompt):
            self._trace_log.append("[CHART] Detected chart request")

            if not file_path:
                self._trace_log.append("[ERROR] No file path for chart")
                return "Error: Please upload a file first before requesting a chart."

            chart_result = self.generate_chart_direct(file_path, prompt)
            if chart_result.startswith("data:image/png;base64,"):
                return chart_result
            else:
                return chart_result

        # TEXT REQUEST: Check cache first
        cache_key = self._get_cache_key(prompt, file_path)
        if cache_key in self._cache:
            self._trace_log.append("[CACHE] Hit")
            return self._cache[cache_key]

        # Try Groq FIRST (primary, cheap, high quota)
        if self._groq is not None:
            self._trace_log.append("[GROQ] Attempting primary LLM call")
            try:
                groq_response = self._groq.generate(prompt, self._build_system_prompt())
                if groq_response and not groq_response.startswith("Groq error"):
                    self._trace_log.append(f"[GROQ] Success: {len(groq_response)} chars")
                    self._cache[cache_key] = groq_response
                    return groq_response
                else:
                    self._trace_log.append(f"[GROQ] Failed: {groq_response}")
            except Exception as e:
                self._trace_log.append(f"[GROQ] Exception: {str(e)}")

        # Fallback to ADK/Gemini
        self._trace_log.append("[ADK] Falling back to Gemini")
        try:
            async def _arun() -> list[str]:
                await self._ensure_session()

                content = types.Content(
                    role="user",
                    parts=[types.Part(text=prompt)]
                )

                responses: list[str] = []
                async for event in self._runner.run_async(
                    user_id=self.user_id,
                    session_id=self.session_id,
                    new_message=content,
                ):
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                responses.append(part.text)

                return responses

            responses = asyncio.run(_arun())

            if responses:
                result = "\n".join(responses)
                self._trace_log.append(f"[ADK] Gemini response: {len(result)} chars")
                self._cache[cache_key] = result
                return result

        except Exception as e:
            error_str = str(e)
            self._trace_log.append(f"[ADK] Gemini failed: {error_str[:200]}")

            if self._groq is None:
                return (
                    f"Error: All LLM services unavailable. {error_str}. "
                    "Please check your API keys and rate limits."
                )

        return (
            "I could not generate a response. Please ensure your API keys are valid "
            "and try again."
        )

    def get_trace(self) -> str:
        """Return the execution trace."""
        return "\n".join(self._trace_log)