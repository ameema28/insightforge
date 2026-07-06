"""
InsightForge Runner — Production Version

For file-based queries: Returns direct structured markdown with real data.
Groq is used ONLY for general chat without files.
"""

import re
import os
import hashlib
from pathlib import Path
from typing import Optional, Tuple

from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=str(env_path))
else:
    load_dotenv()

from agents.tools import analyze_csv, generate_chart, data_quality_report

try:
    from groq import Groq as _GroqClient
    Groq = _GroqClient
    GROQ_AVAILABLE = True
except ImportError:
    Groq = None
    GROQ_AVAILABLE = False


class GroqWrapper:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key or "your" in api_key.lower() or len(api_key) < 20:
            raise ValueError("Invalid GROQ_API_KEY")
        if Groq is None:
            raise ImportError("Groq not installed")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

    def ask(self, system: str, user: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.5, max_tokens=2048, timeout=30,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[Groq Error: {str(e)}]"


class InsightForgeRunner:
    def __init__(self, session_id: str = "streamlit_user_001"):
        self.session_id = session_id
        self._trace_log: list[str] = []
        self._cache: dict[str, str] = {}
        self._groq: Optional[GroqWrapper] = None
        if GROQ_AVAILABLE and os.getenv("GROQ_API_KEY"):
            try:
                self._groq = GroqWrapper()
            except Exception:
                pass

    def _is_chart_request(self, prompt: str) -> bool:
        return any(kw in prompt.lower() for kw in ['chart', 'graph', 'plot', 'visualize', 'bar chart', 'line chart', 'scatter', 'histogram'])

    def _is_summary_request(self, prompt: str) -> bool:
        return any(kw in prompt.lower() for kw in ['summary', 'summarize', 'executive', 'manager', 'brief', 'overview'])

    def _is_quality_request(self, prompt: str) -> bool:
        return any(kw in prompt.lower() for kw in [
            'quality', 'schema', 'columns', 'data types', 'dtype',
            'missing', 'duplicate', 'profile', 'encoding', 'delimiter',
            'clean', 'inspect', 'structure'
        ])

    def _extract_file_path(self, prompt: str) -> Optional[str]:
        if '(File:' in prompt:
            return prompt.split('(File:')[1].split(')')[0].strip()
        return None

    def _detect_columns(self, df, prompt: str) -> Tuple[str, str]:
        import pandas as pd
        prompt_lower = prompt.lower()
        cols = list(df.columns)
        mentioned = [c for c in cols if c.lower() in prompt_lower]
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        x_col, y_col = "", ""
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

    def _get_cache_key(self, prompt: str, file_path: Optional[str]) -> str:
        return hashlib.md5(f"{prompt}:{file_path or ''}".encode()).hexdigest()

    def _format_as_markdown(self, raw_report: str, prompt: str) -> str:
        lines = raw_report.strip().split('\n')
        formatted = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if set(stripped) <= set('=-'):
                continue
            if stripped == 'DATA SCOUT REPORT':
                formatted.append(f"## {stripped}")
            elif stripped == 'NUMERIC SUMMARY':
                formatted.append(f"\n## {stripped}")
            elif stripped == 'PRODUCT-LEVEL BREAKDOWN':
                formatted.append(f"\n## {stripped}")
            elif stripped == 'REGION-LEVEL BREAKDOWN':
                formatted.append(f"\n## {stripped}")
            elif stripped == 'DATA QUALITY FLAGS':
                formatted.append(f"\n## {stripped}")
            elif stripped.endswith(':') and not stripped.startswith('  '):
                formatted.append(f"\n**{stripped}**")
            elif stripped.startswith('  '):
                formatted.append(stripped)
            else:
                formatted.append(stripped)
        result = "\n\n".join(formatted)
        header = f"# Analysis Result\n\n**Question:** {prompt}\n\n"
        footer = "\n\n---\n\n*Powered by InsightForge multi-agent BI system*"
        return header + result + footer

    def _format_quality_markdown(self, report: str, prompt: str) -> str:
        """Render the robust-loader report as camera-friendly markdown."""
        lines = [l.rstrip() for l in report.split("\n")]
        q = prompt.split("(File:")[0].strip()
        out = [f"### Data Quality Report", f"*{q}*", ""]
        meta = {}
        schema_rows, flags = [], []
        score_line, dims_line, section = "", "", None
        for l in lines:
            st = l.strip()
            if not st or set(st) <= set("=-"):
                continue
            if st.startswith("DATA SCOUT REPORT"):
                continue
            if st.startswith("File:"):
                meta["File"] = st.split("File:")[1].strip(); continue
            if st.startswith("Encoding:"):
                meta["enc"] = st; continue
            if st.startswith("Rows:"):
                meta["rows"] = st; continue
            if st.startswith("DATA QUALITY SCORE:"):
                score_line = st.split("DATA QUALITY SCORE:")[1].strip(); continue
            if st.startswith("completeness="):
                dims_line = st; continue
            if st == "SCHEMA":
                section = "schema"; continue
            if st == "FLAGS":
                section = "flags"; continue
            if section == "schema" and "::" in st:
                schema_rows.append(st); continue
            if section == "flags" and st.startswith("-"):
                flags.append(st.lstrip("- ").strip()); continue
        out.append(f"## {score_line}")
        if dims_line:
            parts = dict(x.split("=") for x in dims_line.split())
            out.append(
                f"**Completeness** {parts.get('completeness','')} \u00b7 "
                f"**Uniqueness** {parts.get('uniqueness','')} \u00b7 "
                f"**Validity** {parts.get('validity','')} \u00b7 "
                f"**Consistency** {parts.get('consistency','')}"
            )
        out.append("")
        m = [meta.get("File", "")]
        if meta.get("enc"): m.append(meta["enc"])
        if meta.get("rows"): m.append(meta["rows"])
        out.append("  |  ".join(x for x in m if x))
        out.append("")
        if schema_rows:
            out += ["**Schema**", "", "| Column | Type | Missing | Unique |", "|---|---|---|---|"]
            for r in schema_rows:
                name = r.split("::")[0].strip()
                rest = r.split("::")[1]
                dtype = rest.split("|")[0].strip()
                missing, unique = "0%", ""
                for seg in rest.split("|"):
                    seg = seg.strip()
                    if seg.startswith("missing"): missing = seg.replace("missing", "").strip()
                    if seg.startswith("unique"): unique = seg.replace("unique", "").strip()
                out.append(f"| {name} | `{dtype}` | {missing} | {unique} |")
            out.append("")
        if flags:
            out += ["**Data Quality Flags**", ""]
            for f in flags:
                out.append(f"- {f}")
            out.append("")
        return "\n".join(out)

    def generate_chart_direct(self, file_path: str, prompt: str) -> str:
        import pandas as pd
        self._trace_log.append(f"[CHART] Reading: {file_path}")
        try:
            df = pd.read_csv(file_path) if file_path.lower().endswith(".csv") else pd.read_excel(file_path)
        except Exception as e:
            return f"Error: {str(e)}"
        self._trace_log.append(f"[CHART] {len(df)} rows, cols: {list(df.columns)}")
        x_col, y_col = self._detect_columns(df, prompt)
        self._trace_log.append(f"[CHART] x={x_col}, y={y_col}")
        chart_type = 'bar'
        if any(kw in prompt.lower() for kw in ['line', 'trend']):
            chart_type = 'line'
        elif any(kw in prompt.lower() for kw in ['scatter', 'correlation']):
            chart_type = 'scatter'
        result = generate_chart(file_path, x_col, y_col, chart_type)
        if result.startswith("data:image/png;base64,"):
            self._trace_log.append("[CHART] SUCCESS")
            return result
        else:
            self._trace_log.append(f"[CHART] FAILED: {result}")
            return result

    def run(self, prompt: str) -> str:
        self._trace_log = []
        self._trace_log.append(f"[START] {prompt[:60]}...")
        file_path = self._extract_file_path(prompt)
        if not file_path:
            self._trace_log.append("[CHAT] No file")
            if self._groq:
                resp = self._groq.ask("You are InsightForge, a helpful data analyst.", prompt)
                self._trace_log.append(f"[CHAT] {len(resp)} chars")
                return resp
            return "Please upload a CSV/Excel file or configure a valid GROQ_API_KEY."
        if self._is_chart_request(prompt):
            self._trace_log.append("[CHART] Request")
            return self.generate_chart_direct(file_path, prompt)
        if self._is_quality_request(prompt):
            self._trace_log.append("[SCOUT] Data-quality request")
            cache_key = self._get_cache_key(prompt, file_path)
            if cache_key in self._cache:
                self._trace_log.append("[CACHE] Hit")
                return self._cache[cache_key]
            report = data_quality_report(file_path)
            self._trace_log.append(f"[TOOL] data_quality_report: {len(report)} chars")
            if report.startswith("SECURITY_ERROR") or report.startswith("PROCESSING_ERROR"):
                return report
            final = self._format_quality_markdown(report, prompt)
            self._cache[cache_key] = final
            return final
        self._trace_log.append(f"[ANALYSIS] File: {file_path}")
        cache_key = self._get_cache_key(prompt, file_path)
        if cache_key in self._cache:
            self._trace_log.append("[CACHE] Hit")
            return self._cache[cache_key]
        raw_report = analyze_csv(file_path)
        self._trace_log.append(f"[TOOL] analyze_csv: {len(raw_report)} chars")
        if raw_report.startswith("SECURITY_ERROR") or raw_report.startswith("PROCESSING_ERROR"):
            return raw_report
        final = self._format_as_markdown(raw_report, prompt)
        self._trace_log.append(f"[RESULT] Direct markdown: {len(final)} chars")
        self._cache[cache_key] = final
        return final

    def get_trace(self) -> str:
        return "\n".join(self._trace_log)