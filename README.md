# InsightForge

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Google ADK](https://img.shields.io/badge/Built%20with-Google%20ADK-orange)](https://developers.google.com/adk)
[![MCP](https://img.shields.io/badge/Protocol-MCP-purple)](https://modelcontextprotocol.io)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-green.svg)](https://creativecommons.org/licenses/by/4.0/)

> **Multi-Agent Business Intelligence System** built with Google ADK & MCP for the [Kaggle AI Agents: Intensive Vibe Coding Capstone 2026](https://www.kaggle.com/competitions/vibecoding-agents-capstone-project) sponsored by Google.

---

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Solution Architecture](#solution-architecture)
- [Key Features](#key-features)
- [Project Timeline](#project-timeline)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Security](#security)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [License](#license)
- [Author](#author)

---

## Overview

InsightForge is a production-grade multi-agent system that transforms raw business data into executive-ready reports through natural language. It demonstrates the application of Google ADK, Model Context Protocol (MCP), and enterprise security practices to solve real-world business intelligence challenges.

The system was developed as the capstone project for the [Kaggle AI Agents: Intensive Vibe Coding Course with Google](https://www.kaggle.com/competitions/vibecoding-agents-capstone-project), covering a 5-day intensive curriculum on agent design, tool interoperability, security, and deployment.

---

## Problem Statement

Business analysts spend approximately 40% of their time on repetitive data tasks: formatting CSVs, writing manual SQL queries, and generating static reports. Non-technical managers are blocked from accessing insights without engineering support. InsightForge automates this entire pipeline using a secure, multi-agent architecture that reasons about data, validates quality, and produces actionable summaries autonomously.

---

## Solution Architecture

```
User (Streamlit UI)
    |
    v
+---------------------+
|  InsightForgeRunner |  <-- Sync bridge over async ADK Runner
|  (Streamlit Bridge) |
+----------+----------+
           |
           v
+---------------------+
|  Orchestrator Agent |  <-- Routes tasks, manages session state
|     (ADK)           |
+------+------+-------+
       |      |
       v      v
+----------+  +--------------+
|Data Scout|  |   Analyst    |
|  Agent   |  |    Agent     |
|          |  |              |
|MCP Tools:|  |MCP Tools:    |
|- validate|  |- describe    |
|- load    |  |- correlate   |
|- quality |  |- visualize   |
+----------+  +--------------+
       |              |
       +------+-------+
              |
              v
       +--------------+
       | Report Writer|
       |    Agent       |
       |              |
       |- summarize   |
       |- recommend   |
       +--------------+
```

**Design Philosophy:**
- **Orchestrator Pattern:** A central router delegates tasks to specialist agents, mirroring enterprise microservices architecture.
- **Tool Interoperability:** All data tools are exposed via MCP, enabling reuse across any MCP-compatible framework.
- **Defense in Depth:** Security guardrails operate at every layer: input validation, PII redaction, and output sanitization.
- **Streamlit Integration:** A synchronous runner bridge (`InsightForgeRunner`) connects the async ADK pipeline to the Streamlit frontend.

---

## Key Features

### Day 1: Foundation Agent
- Single ADK agent with natural language data analysis
- `analyze_csv` tool: automated data profiling, schema detection, missing value reporting
- `generate_chart` tool: matplotlib visualization generation (bar, line, scatter)
- Enterprise-grade security: file extension whitelist, path traversal protection, PII redaction
- 13 pytest test cases covering security, data tools, and agent initialization

### Day 2: MCP Server
- Standalone MCP server exposing all data tools via the Model Context Protocol
- Compatible with any MCP client: ADK, Claude Desktop, Cursor, custom implementations
- `analyze_csv_tool` and `generate_chart_tool` available via JSON-RPC over stdio
- 6 MCP-specific test cases verifying protocol compliance and tool functionality
- Full protocol documentation in `docs/MCP_GUIDE.md`

### Day 3: Multi-Agent Architecture
- **Orchestrator Agent:** Central router that interprets user intent and delegates to specialists
- **Data Scout Agent:** Loads data, validates schema, reports quality issues
- **Analyst Agent:** Performs statistical analysis, generates visualizations, identifies trends
- **Report Writer Agent:** Converts technical findings into executive summaries with recommendations
- 7 multi-agent tests verifying agent hierarchy, tool wiring, and model configuration
- Full delegation chain demonstrated in ADK Web UI with trace visualization

### Day 4: Streamlit Frontend & Runner Bridge
- **Streamlit UI:** File upload (CSV/Excel), chat interface with message history, session info sidebar
- **InsightForgeRunner:** Synchronous bridge over async ADK `Runner` for Streamlit compatibility
- **MemoryBank:** JSON-based session persistence so uploaded files and preferences survive reruns
- **Security Integration:** Prompt injection guardrails and rate limiting applied before every request

### Planned (Days 5-7)
- Day 5: Security hardening (output sanitization, advanced injection patterns)
- Day 6: Cloud Run deployment with public endpoint
- Day 7: 5-minute YouTube demo and Kaggle submission

---

## Project Timeline

| Day | Focus | Deliverable | Status |
|-----|-------|-------------|--------|
| Day 1 | Foundation Agent | Single ADK agent with security-first data tools | Complete |
| Day 2 | MCP Server | Standalone protocol server for tool interoperability | Complete |
| Day 3 | Multi-Agent System | Orchestrator + 3 specialist agents with delegation | Complete |
| Day 4 | Memory & Frontend | Streamlit UI with ADK runner bridge and session memory | Complete |
| Day 5 | Security Hardening | Prompt injection guardrails, rate limiting, PII filters | Planned |
| Day 6 | Deployment | Cloud Run containerization and live URL | Planned |
| Day 7 | Video & Writeup | 5-minute YouTube demo and Kaggle submission | Planned |

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Agent Framework | Google ADK | Multi-agent orchestration and lifecycle management |
| Tool Protocol | MCP (Model Context Protocol) | Universal tool interface for cross-framework compatibility |
| LLM | Gemini 2.5 Flash | Natural language reasoning and task planning |
| Data Processing | pandas, openpyxl | CSV/Excel ingestion and manipulation |
| Visualization | matplotlib, seaborn | Chart and graph generation |
| Frontend | Streamlit | User-facing web interface |
| Cloud | Google Cloud Run | Serverless deployment |
| Dev Environment | Antigravity IDE | Agent-first development workspace |
| Testing | pytest | Unit and integration test suite |

---

## Project Structure

```
insightforge/
├── app.py                    # Streamlit frontend (Day 4)
├── agents/                   # ADK Multi-Agent Application
│   ├── __init__.py           # Exports orchestrator as root_agent
│   ├── orchestrator.py       # Central router (Day 3)
│   ├── data_scout.py         # Data loading & validation specialist (Day 3)
│   ├── analyst.py            # Statistical analysis & visualization (Day 3)
│   ├── report_writer.py      # Executive summary generation (Day 3)
│   ├── agent.py              # Legacy single-agent foundation (Day 1)
│   ├── tools.py              # Data analysis tools with security guardrails
│   ├── runner.py             # Streamlit sync bridge over ADK Runner (Day 4)
│   └── memory.py             # JSON-based session persistence (Day 4)
├── mcp_server/               # Model Context Protocol Server (Day 2)
│   └── server.py
├── security/                 # Security guardrails
│   ├── __init__.py
│   └── guardrails.py         # Prompt injection, rate limiting, validation
├── tests/                    # pytest Test Suite
│   ├── test_day1.py          # Foundation agent tests (13 cases)
│   ├── test_mcp_server.py    # MCP protocol tests (6 cases)
│   ├── test_multi_agent.py   # Multi-agent hierarchy tests (7 cases)
│   └── test_security.py      # Security guardrail tests
├── docs/                     # Documentation
│   ├── RECORDING_GUIDE.md    # Competition video production schedule
│   ├── GIT_WORKFLOW.md       # Professional Git practices
│   ├── MCP_GUIDE.md          # Protocol architecture documentation
│   └── WRITEUP.md            # Kaggle submission writeup template
├── deployment/               # Cloud Run Configuration (Day 6)
│   └── cloudbuild.yaml
├── requirements.txt          # Python dependencies
├── pytest.ini               # Test configuration
├── .env.example             # Environment variable template
├── .gitignore               # Git exclusion rules
├── Dockerfile               # Container image definition (Day 4)
├── .dockerignore            # Docker build exclusions (Day 4)
├── root_agent.py            # Root-level agent re-export for CLI
├── sample_sales.csv         # Demo dataset
└── README.md                # This file
```

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [Google AI Studio API Key](https://aistudio.google.com/app/apikey)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/ameema28/insightforge.git
cd insightforge

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and paste your GOOGLE_API_KEY
```

---

## Usage

### Streamlit Frontend (Day 4)

Launch the web UI and interact with the full agent chain:

```bash
streamlit run app.py
```

1. Upload `sample_sales.csv` via the sidebar
2. Type a natural language request:

> *"Show me revenue by region as a bar chart"*

The Orchestrator automatically delegates:
1. **Data Scout** loads and validates the file
2. **Analyst** generates insights and charts
3. **Report Writer** produces an executive summary

### Multi-Agent System (Day 3)

Launch via ADK Web for trace visualization:

```bash
adk web
```

1. Select **"agents"** from the app list
2. Select **"insightforge_orchestrator"**
3. Click **"New Session"**
4. Type a natural language request

### MCP Server (Day 2)

Run the standalone protocol server:

```bash
# Stdio transport mode
python mcp_server/server.py

# Or inspect with MCP dev tools
mcp dev mcp_server/server.py
```

### Single Agent (Day 1 Legacy)

For backward compatibility:

```bash
adk run root_agent
```

---

## Security

InsightForge implements defense-in-depth security for production agent deployments:

| Layer | Implementation | Location |
|-------|---------------|----------|
| Input Validation | File extension whitelist (`.csv`, `.xlsx`, `.xls`), path normalization | `agents/tools.py` |
| PII Redaction | Regex-based detection and masking of emails, phone numbers, SSNs | `agents/tools.py` |
| Prompt Injection | Rejection of instructions attempting to override system behavior | `security/guardrails.py` |
| Rate Limiting | Per-session request throttling | `security/guardrails.py` |

---

## Testing

Run the full test suite:

```bash
pytest -v
```

**Current Coverage:**
- 13 foundation agent tests (security, data tools, agent initialization)
- 6 MCP server tests (protocol compliance, tool functionality)
- 7 multi-agent tests (hierarchy, tool wiring, model configuration)
- **Total: 26 tests**

---

## Deployment

### Local Docker Test

```bash
docker build -t insightforge .
docker run -p 8080:8080 -e GOOGLE_API_KEY=your_key insightforge
```

### Cloud Run (Day 6)

```bash
gcloud builds submit --config deployment/cloudbuild.yaml \
  --substitutions=_GOOGLE_API_KEY=your_api_key
```

- **Live Demo:** Coming soon (Day 6)
- **Video Demo:** Coming soon (Day 7)
- **Kaggle Writeup:** [Draft created](https://www.kaggle.com/competitions/vibecoding-agents-capstone-project)

---

## Documentation

| Document | Description |
|----------|-------------|
| `docs/RECORDING_GUIDE.md` | Daily recording schedule and video production guide for the 5-minute competition submission |
| `docs/GIT_WORKFLOW.md` | Professional Git practices, commit conventions, and portfolio optimization |
| `docs/MCP_GUIDE.md` | Model Context Protocol architecture, usage examples, and integration patterns |
| `docs/WRITEUP.md` | Kaggle submission writeup template (under 2,500 words) |

---

## License

This project is licensed under [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/), as required by the Kaggle competition rules.

---

## Author

**Ameema Rashid**
- GitHub: [@ameema28](https://github.com/ameema28)
- Project: [InsightForge](https://github.com/ameema28/insightforge)
- Competition: [Kaggle AI Agents Capstone 2026](https://www.kaggle.com/competitions/vibecoding-agents-capstone-project)

Built for the Kaggle AI Agents: Intensive Vibe Coding Capstone 2026 sponsored by Google.
