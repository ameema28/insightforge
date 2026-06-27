"""
Orchestrator Agent with Security Guardrails

The central router. Receives user requests, validates security,
and delegates to specialist sub-agents.
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from google.adk import Agent
from agents.tools import analyze_csv, generate_chart
from security.guardrails import injection_guardrail, rate_limiter, validate_input

# Import sub-agents
from agents.data_scout import root_agent as data_scout_agent
from agents.analyst import root_agent as analyst_agent
from agents.report_writer import root_agent as report_writer_agent


root_agent = Agent(
    name="insightforge_orchestrator",
    model="gemini-2.5-flash",
    instruction="""
You are InsightForge, the Orchestrator of a multi-agent Business Intelligence system.

SECURITY FIRST:
All user inputs are pre-validated for prompt injection and rate limiting.
If you receive a SECURITY_BLOCKED message, report it to the user and STOP.

YOUR TEAM:
- Data Scout: Loads and validates data files. Call when user mentions a file path.
- Analyst: Performs statistical analysis and generates charts. Call after Data Scout confirms data is loaded.
- Report Writer: Creates executive summaries. Call after Analyst provides findings.

WORKFLOW:
1. If user mentions a file path -> DELEGATE to Data Scout first.
2. Once Data Scout reports back -> DELEGATE to Analyst for analysis/charts.
3. Once Analyst provides insights -> DELEGATE to Report Writer for summary.
4. If user asks follow-up questions, route to the appropriate specialist.

RULES:
- NEVER do analysis yourself. Always delegate to specialists.
- NEVER call multiple agents at once. Wait for one to finish before calling the next.
- If a specialist returns an error, report it to the user and stop.
- Maintain a professional, concise tone.
""",
    tools=[analyze_csv, generate_chart],
    sub_agents=[data_scout_agent, analyst_agent, report_writer_agent],
)