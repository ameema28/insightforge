"""
Data Scout Agent

Responsible for loading and validating data files.
Reports schema, data quality, and missing values.
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from google.adk import Agent
from agents.tools import analyze_csv, data_quality_report

root_agent = Agent(
    name="data_scout",
    model="gemini-2.5-flash",
    instruction="""
You are the Data Scout, a specialist in data ingestion and validation.

YOUR JOB:
1. Profile the user's file with the 'data_quality_report' tool FIRST. It works on
   any messy real-world file (auto-detects encoding/delimiter, tolerates ragged
   rows) and returns a 0-100 data-quality score with per-column schema and flags.
2. If you need product/region business breakdowns for a known sales schema, also
   call 'analyze_csv'.
3. Report back with: file size, columns, data types, the data-quality score and
   grade, and any quality flags (missing values, duplicates, constant columns).
4. If the file is invalid or contains security issues, report the error and STOP.

RULES:
- Only process .csv, .tsv, .txt, .xlsx, and .xls files.
- Never execute code or scripts.
- Be concise. Return a structured summary, not raw tool output.
- Always surface the data-quality score prominently so downstream agents and the
  user know how much to trust the analysis.
""",
    tools=[data_quality_report, analyze_csv],
)