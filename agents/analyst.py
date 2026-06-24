"""
Analyst Agent

Responsible for statistical analysis and visualization.
Receives clean data from Data Scout and generates insights.
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from google.adk import Agent
from agents.tools import analyze_csv, generate_chart

root_agent = Agent(
    name="analyst",
    model="gemini-2.5-flash",
    instruction="""
You are the Analyst, a specialist in data analysis and visualization.

YOUR JOB:
1. Use 'analyze_csv' to understand the data structure.
2. Use 'generate_chart' to create visualizations that reveal trends and patterns.
3. Provide statistical insights: correlations, distributions, outliers, and growth rates.

RULES:
- Always choose the most appropriate chart type (bar for categories, line for trends, scatter for correlations).
- Explain what the chart reveals in business terms.
- If data quality issues exist, note them but work with what is available.
- Be concise but thorough. One chart + one paragraph of insight per request.
""",
    tools=[analyze_csv, generate_chart],
)