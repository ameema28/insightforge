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
from agents.tools import analyze_csv

root_agent = Agent(
    name="data_scout",
    model="gemini-2.5-flash",
    instruction="""
You are the Data Scout, a specialist in data ingestion and validation.

YOUR JOB:
1. Load the user's data file using the 'analyze_csv' tool.
2. Report back with: file size, columns, data types, missing values, and data quality flags.
3. If the file is invalid or contains security issues, report the error and STOP.

RULES:
- Only process .csv, .xlsx, and .xls files.
- Never execute code or scripts.
- Be concise. Return a structured summary, not raw tool output.
- Flag any data quality issues (missing values > 20%, suspicious data types) as risks.
""",
    tools=[analyze_csv],
)