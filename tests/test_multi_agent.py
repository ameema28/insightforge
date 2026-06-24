"""
Tests for InsightForge Multi-Agent System.

Verifies that the Orchestrator correctly delegates to specialist agents
and that the agent hierarchy is properly configured.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.orchestrator import root_agent as orchestrator
from agents.data_scout import root_agent as data_scout
from agents.analyst import root_agent as analyst
from agents.report_writer import root_agent as report_writer


class TestAgentHierarchy:
    """Verify the multi-agent architecture is correctly wired."""

    def test_orchestrator_name(self):
        """Orchestrator should have the correct name."""
        assert orchestrator.name == "insightforge_orchestrator"

    def test_orchestrator_has_sub_agents(self):
        """Orchestrator must have 3 sub-agents."""
        assert hasattr(orchestrator, "sub_agents")
        assert len(orchestrator.sub_agents) == 3

    def test_sub_agent_names(self):
        """Sub-agents should be named correctly."""
        names = [agent.name for agent in orchestrator.sub_agents]
        assert "data_scout" in names
        assert "analyst" in names
        assert "report_writer" in names

    def test_data_scout_tools(self):
        """Data Scout should have analyze_csv tool."""
        assert len(data_scout.tools) >= 1
        tool_names = [t.__name__ if hasattr(t, '__name__') else t.name for t in data_scout.tools]
        assert "analyze_csv" in tool_names

    def test_analyst_tools(self):
        """Analyst should have both analysis tools."""
        assert len(analyst.tools) >= 2
        tool_names = [t.__name__ if hasattr(t, '__name__') else t.name for t in analyst.tools]
        assert "analyze_csv" in tool_names
        assert "generate_chart" in tool_names

    def test_report_writer_no_tools(self):
        """Report Writer should have no tools (pure summarization)."""
        assert len(report_writer.tools) == 0

    def test_all_agents_use_gemini(self):
        """All agents should use Gemini 2.5 Flash."""
        for agent in [orchestrator, data_scout, analyst, report_writer]:
            assert agent.model == "gemini-2.5-flash"