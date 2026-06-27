"""
InsightForge Agent Tracer

Captures agent execution events and formats them for display.
Provides real-time visibility into the multi-agent delegation chain.
"""

import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class AgentEvent:
    """Single event in the agent execution trace."""
    timestamp: str
    agent_name: str
    event_type: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


class AgentTracer:
    """
    Collects and formats agent execution traces.
    Singleton pattern for cross-agent visibility.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentTracer, cls).__new__(cls)
            cls._instance._events = []
            cls._instance._active = True
        return cls._instance

    def log(self, agent_name, event_type, message, details=None):
        """Record an event if tracing is active."""
        if not self._active:
            return

        event = AgentEvent(
            timestamp=time.strftime("%H:%M:%S"),
            agent_name=agent_name,
            event_type=event_type,
            message=message,
            details=details if details is not None else {}
        )
        self._events.append(event)

    def get_trace(self):
        """Return all events as dictionaries."""
        return [asdict(e) for e in self._events]

    def get_formatted_trace(self):
        """Return a human-readable formatted trace."""
        lines = []
        lines.append("=" * 60)
        lines.append("AGENT EXECUTION TRACE")
        lines.append("=" * 60)

        for event in self._events:
            icon = {
                "start": ">",
                "tool_call": "[T]",
                "tool_result": "[R]",
                "delegate": "->",
                "complete": "[OK]",
                "error": "[ERR]"
            }.get(event.event_type, "*")

            lines.append(f"\n[{event.timestamp}] {icon} {event.agent_name}")
            lines.append(f"    {event.event_type.upper()}: {event.message}")
            if event.details:
                for k, v in event.details.items():
                    lines.append(f"    * {k}: {v}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

    def clear(self):
        """Reset the trace."""
        self._events = []

    def set_active(self, active):
        """Enable or disable tracing."""
        self._active = active


# Global tracer instance
tracer = AgentTracer()