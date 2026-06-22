# InsightForge

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Google ADK](https://img.shields.io/badge/Built%20with-Google%20ADK-orange)](https://developers.google.com/adk)
[![MCP](https://img.shields.io/badge/Protocol-MCP-purple)](https://modelcontextprotocol.io)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-green.svg)](https://creativecommons.org/licenses/by/4.0/)

> **Multi-Agent Business Intelligence System** built with Google ADK & MCP for the [Kaggle AI Agents: Intensive Vibe Coding Capstone 2026](https://www.kaggle.com/competitions/vibecoding-agents-capstone-project).

---

## Problem Statement

Business analysts spend ~40% of their time on repetitive data formatting, manual SQL queries, and report generation. Non-technical managers are blocked from getting insights without engineering support. InsightForge automates this entire pipeline using a secure, multi-agent architecture.

## Solution Overview

InsightForge is a production-grade agent system that turns raw business data into executive-ready reports through natural language:

1. **Upload** a CSV/Excel file
2. **Ask** in plain English: *"Why did Q2 revenue drop? Generate a board-ready report."*
3. **Receive** a validated analysis, visualizations, and actionable recommendations

## Architecture

```
User (Streamlit UI)
    │
    ▼
┌─────────────────────┐
│  Orchestrator Agent │  ← Routes tasks, manages session memory
│     (ADK)           │
└──────┬──────┬──────┘
       │      │
       ▼      ▼
┌──────────┐  ┌──────────────┐
│Data Scout│  │   Analyst    │
│  Agent   │  │    Agent     │
│          │  │              │
│MCP Tools:│  │MCP Tools:    │
│- validate│  │- describe    │
│- load    │  │- correlate   │
│- quality │  │- visualize   │
└──────────┘  └──────────────┘
       │              │
       └──────┬───────┘
              ▼
       ┌──────────────┐
       │ Report Writer│
       │    Agent       │
       │              │
       │- summarize   │
       │- recommend   │
       └──────────────┘
```

## Key Concepts Demonstrated (Course Requirements)

| Concept | Where Demonstrated | Evidence |
|---------|-------------------|----------|
| **Agent / Multi-Agent System (ADK)** | `agents/` directory | Orchestrator + 3 sub-agents with `google-adk` |
| **MCP Server** | `mcp_server/` | Custom MCP server exposing data analysis tools |
| **Antigravity** | Video | Development and agent testing in Antigravity IDE |
| **Security Features** | `agents/tools.py`, `security/` | Input validation, PII redaction, prompt injection guardrails |
| **Deployability** | `deployment/`, Live URL | Cloud Run deployment with public endpoint |
| **Agent Skills (Agents CLI)** | `.agent/skills/` | `google-agents-cli` scaffolded reusable skills |

## Tech Stack

- **Framework**: [Google ADK](https://developers.google.com/adk) (Agent Development Kit)
- **Protocol**: [MCP](https://modelcontextprotocol.io) (Model Context Protocol)
- **LLM**: Gemini 2.5 Flash via Google AI Studio
- **Data**: pandas, matplotlib, seaborn, openpyxl
- **Frontend**: Streamlit
- **Cloud**: Google Cloud Run
- **Dev Environment**: Antigravity IDE

## Project Structure

```
insightforge/
├── agents/                    # ADK Agent App (self-contained)
│   ├── __init__.py           # Exports root_agent for ADK discovery
│   ├── agent.py              # Agent definition (root_agent)
│   └── tools.py              # Data analysis tools (self-contained)
├── tests/                    # pytest suite
│   └── test_day1.py
├── docs/                     # Documentation
│   ├── RECORDING_GUIDE.md
│   └── GIT_WORKFLOW.md
├── deployment/               # Cloud Run config (Day 12)
│   └── README.md
├── mcp_server/               # MCP server (Day 2)
│   └── .gitkeep
├── requirements.txt
├── pytest.ini
├── .env.example
├── .gitignore
├── README.md
├── root_agent.py             # Root-level re-export for CLI
└── sample_sales.csv
```

## Quick Start

### Prerequisites

- Python 3.10 or higher
- [Google AI Studio API Key](https://aistudio.google.com/app/apikey)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/insightforge.git
cd insightforge

# Create virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and paste your GOOGLE_API_KEY
```

### Running the Agent (Day 1)

```bash
# Web UI mode (recommended for testing)
adk web
# Then select 'agents' from the app list and start a New Session

# Interactive CLI mode (alternative)
adk run root_agent
```

**Test it:**
> *"Analyze the file sample_sales.csv"*

### Running Tests

```bash
pytest -v
```

## Security

InsightForge implements defense-in-depth for production agent safety:

- **Input Validation**: File extension whitelist (`.csv`, `.xlsx`, `.xls`), path normalization
- **PII Redaction**: Automatic detection and masking of emails, phone numbers, and SSNs in outputs
- **Prompt Injection Guardrails**: Rejection of instructions attempting to override system behavior
- **Rate Limiting**: Per-session request throttling
- **Output Validation**: Prevention of code execution and malicious payload generation

## Deployment

Deployed to Google Cloud Run for public access. See `deployment/README.md` for full instructions.

- **Live Demo**: [YOUR_CLOUD_RUN_URL_HERE]
- **Video Demo**: [YOUR_YOUTUBE_LINK_HERE]
- **Kaggle Writeup**: [YOUR_KAGGLE_WRITEUP_LINK_HERE]

## License

This project is licensed under [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/), as required by the Kaggle competition rules.

## Acknowledgments

Built for the [Kaggle AI Agents: Intensive Vibe Coding Capstone 2026](https://www.kaggle.com/competitions/vibecoding-agents-capstone-project) sponsored by Google.

## Author
Built by [Ameema Rashid](https://github.com/ameema28) for the Kaggle AI Agents Capstone 2026.