# InsightForge

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Google ADK](https://img.shields.io/badge/Built%20with-Google%20ADK-orange)](https://developers.google.com/adk)
[![MCP](https://img.shields.io/badge/Protocol-MCP-purple)](https://modelcontextprotocol.io)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-green.svg)](https://creativecommons.org/licenses/by/4.0/)

&gt; **Multi-Agent Business Intelligence System** built with Google ADK & MCP for the [Kaggle AI Agents: Intensive Vibe Coding Capstone 2026](https://www.kaggle.com/competitions/vibecoding-agents-capstone-project) sponsored by Google.

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


**Design Philosophy:**
- **Orchestrator Pattern:** A central router delegates tasks to specialist agents, mirroring enterprise microservices architecture.
- **Tool Interoperability:** All data tools are exposed via MCP, enabling reuse across any MCP-compatible framework.
- **Defense in Depth:** Security guardrails operate at every layer: input validation, output sanitization, PII redaction, prompt injection detection, and rate limiting.
- **Streamlit Integration:** A synchronous runner bridge (`InsightForgeRunner`) connects the async ADK pipeline to the Streamlit frontend.
- **API Resilience:** Groq API is primary for text generation (20 req/min free tier); Gemini is fallback for ADK multi-agent traces. In-memory caching reduces redundant API calls.

---

## Key Features

### Real-World Data Ingestion (schema-agnostic)
- Robust `data_loader` engine (`agents/data_loader.py`) that handles messy, real business files:
  auto-detects **encoding** (charset-normalizer) and **delimiter** (comma/semicolon/tab/pipe),
  tolerates **quoted fields with embedded newlines** and **ragged rows**, reads **multi-sheet Excel**,
  and **chunks files over 100 MB**.
- **Data-quality score (0–100)** across completeness, uniqueness, validity, and consistency, with a
  letter grade and human-readable flags (missing data, duplicate rows, constant/junk columns).
- Automatic type inference (numeric / datetime) with a 90%-agreement threshold to avoid false positives.
- Exposed to agents and third parties as the `data_quality_report` tool (also over MCP), so the
  Data Scout can profile *any* file — not just the sample schema.
- 25 pytest cases in `tests/test_data_loader.py` covering encoding, delimiters, messy data,
  type inference, the quality score, and Excel.

### Day 1: Foundation Agent
- Single ADK agent with natural language data analysis
- `analyze_csv` tool: automated data profiling, schema detection, missing value reporting
- `generate_chart` tool: matplotlib visualization generation (bar, line, scatter) with base64 output for Streamlit
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
- **Streamlit UI:** File upload (CSV/Excel), chat interface with message history, session info sidebar, API status indicators, chat export
- **InsightForgeRunner:** Synchronous bridge over async ADK `Runner` for Streamlit compatibility
- **MemoryBank:** JSON-based session persistence so uploaded files and preferences survive reruns
- **Security Integration:** Prompt injection guardrails and rate limiting applied before every request

### Day 5: Security Hardening
- **Output Sanitization:** Agent responses are scanned for dangerous content before display
  - Blocks Python, Bash, Shell, PowerShell code blocks
  - Detects and removes HTML script tags and JavaScript protocol handlers
  - Flags system commands (rm -rf, curl, wget, sudo)
  - Prevents API key, password, token, and credit card leakage in outputs
- **PII Redaction:** Automatically masks emails, phone numbers, SSNs, and IP addresses in all outputs
- **User Warning:** Streamlit UI displays a warning banner when output is sanitized
- **10 output sanitizer test cases** verifying detection accuracy and false positive avoidance

### Day 6: Deployment & API Resilience
- **Groq Primary Fallback:** Groq API (llama-3.3-70b) is primary LLM for text generation; Gemini is fallback for ADK traces
- **In-Memory Caching:** Identical prompts return cached responses, reducing API costs
- **Chart Aggregation:** Duplicate x-axis values are automatically summed before plotting
- **Docker Containerization:** Production-ready Dockerfile with healthcheck and security-hardened base image
- **Cloud Run Ready:** Configured for Google Cloud Run serverless deployment with dual API key support

---

## Project Timeline

| Day | Focus | Deliverable | Status |
|-----|-------|-------------|--------|
| Day 1 | Foundation Agent | Single ADK agent with security-first data tools | Complete |
| Day 2 | MCP Server | Standalone protocol server for tool interoperability | Complete |
| Day 3 | Multi-Agent System | Orchestrator + 3 specialist agents with delegation | Complete |
| Day 4 | Memory & Frontend | Streamlit UI with ADK runner bridge and session memory | Complete |
| Day 5 | Security Hardening | Output sanitization, prompt injection, rate limiting, PII filters | Complete |
| Day 6 | Deployment & Resilience | Groq fallback, caching, Docker, Cloud Run config, test sync | Complete |
| Day 7 | Video & Writeup | 5-minute YouTube demo and Kaggle submission | In Progress |

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Agent Framework | Google ADK | Multi-agent orchestration and lifecycle management |
| Tool Protocol | MCP (Model Context Protocol) | Universal tool interface for cross-framework compatibility |
| LLM Primary | Groq (llama-3.3-70b-versatile) | Fast, cost-effective text generation with high rate limits |
| LLM Fallback | Gemini 2.5 Flash | Natural language reasoning and ADK multi-agent traces |
| Data Processing | pandas, openpyxl | CSV/Excel ingestion and manipulation |
| Visualization | matplotlib, seaborn | Chart and graph generation with base64 output |
| Frontend | Streamlit | User-facing web interface |
| Cloud | Google Cloud Run | Serverless deployment |
| Dev Environment | Antigravity IDE | Agent-first development workspace |
| Testing | pytest | Unit and integration test suite (47 tests) |
| Container | Docker | Production containerization with healthcheck |

---

## Project Structure
insightforge/
├── app.py                    # Streamlit frontend (Day 4)
├── agents/                   # ADK Multi-Agent Application
│   ├── init.py           # Exports orchestrator as root_agent
│   ├── orchestrator.py       # Central router (Day 3)
│   ├── data_scout.py         # Data loading & validation specialist (Day 3)
│   ├── analyst.py            # Statistical analysis & visualization (Day 3)
│   ├── report_writer.py      # Executive summary generation (Day 3)
│   ├── agent.py              # Legacy single-agent foundation (Day 1)
│   ├── tools.py              # Data analysis tools with security guardrails
│   ├── runner.py             # Streamlit sync bridge with Groq fallback (Day 6)
│   └── memory.py             # JSON-based session persistence (Day 4)
├── mcp_server/               # Model Context Protocol Server (Day 2)
│   └── server.py
├── security/                 # Security guardrails
│   ├── init.py
│   └── guardrails.py         # Prompt injection, rate limiting, validation, output sanitization (Day 5)
├── tests/                    # pytest Test Suite
│   ├── test_day1.py          # Foundation agent tests (13 cases)
│   ├── test_mcp_server.py    # MCP protocol tests (6 cases)
│   ├── test_multi_agent.py   # Multi-agent hierarchy tests (7 cases)
│   ├── test_security.py      # Security guardrail tests (7 cases)
│   └── test_output_sanitizer.py  # Output sanitization tests (10 cases)
├── tools/                    # Re-exports from agents.tools (Day 6)
│   └── init.py
├── docs/                     # Documentation
│   ├── RECORDING_GUIDE.md    # Competition video production schedule
│   ├── GIT_WORKFLOW.md       # Professional Git practices
│   ├── MCP_GUIDE.md          # Protocol architecture documentation
│   └── WRITEUP.md            # Kaggle submission writeup template
├── deployment/               # Cloud Run Configuration
│   └── cloudbuild.yaml
├── requirements.txt          # Python dependencies
├── pytest.ini               # Test configuration
├── .env.example             # Environment variable template
├── .gitignore               # Git exclusion rules
├── Dockerfile               # Container image definition (Day 6)
├── .dockerignore            # Docker build exclusions (Day 6)
├── root_agent.py            # Root-level agent re-export for CLI
├── sample_sales.csv         # Demo dataset
└── README.md                # This file


---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- [Groq API Key](https://console.groq.com) (free tier: 20 requests/minute)
- [Google AI Studio API Key](https://aistudio.google.com/app/apikey) (fallback)
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
# Edit .env and paste your GROQ_API_KEY and GOOGLE_API_KEY

Usage

Streamlit Frontend
Launch the web UI and interact with the full agent chain:
streamlit run app.py
Upload sample_sales.csv via the sidebar

Type a natural language request:
"Show me revenue by region as a bar chart"

The Orchestrator automatically delegates:
Data Scout loads and validates the file
Analyst generates insights and charts
Report Writer produces an executive summary

Multi-Agent System (ADK Web)
Launch via ADK Web for trace visualization:
adk web
Select "agents" from the app list
Select "insightforge_orchestrator"
Click "New Session"
Type a natural language request

MCP Server
Run the standalone protocol server:
# Stdio transport mode
python mcp_server/server.py
# Or inspect with MCP dev tools
mcp dev mcp_server/server.py

Single Agent (Legacy)
For backward compatibility:
adk run root_agent

Security
InsightForge implements defense-in-depth security for production agent deployments:
| Layer               | Implementation                                                                               | Location                                    |
| ------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------- |
| Input Validation    | File extension whitelist (`.csv`, `.xlsx`, `.xls`), path normalization                       | `agents/tools.py`                           |
| PII Redaction       | Regex-based detection and masking of emails, phone numbers, SSNs, IP addresses, credit cards | `agents/tools.py`, `security/guardrails.py` |
| Prompt Injection    | Rejection of instructions attempting to override system behavior                             | `security/guardrails.py`                    |
| Rate Limiting       | Per-session request throttling                                                               | `security/guardrails.py`                    |
| Output Sanitization | Blocks code blocks, scripts, system commands, API key/token/password/credit card leaks       | `security/guardrails.py`                    |

Testing
Run the full test suite:
pytest -v

Current Coverage: 47 tests
13 foundation agent tests (security, data tools, agent initialization)
6 MCP server tests (protocol compliance, tool functionality)
7 multi-agent tests (hierarchy, tool wiring, model configuration)
7 security guardrail tests (prompt injection, rate limiting, input validation)
10 output sanitizer tests (code block detection, script tag removal, PII redaction, API key leak prevention)

Deployment
Local Docker Test
# Build the image
docker build -t insightforge .

# Run locally
docker run -p 8080:8080 \
  -e GROQ_API_KEY=your_groq_key \
  -e GOOGLE_API_KEY=your_google_key \
  insightforge

Google Cloud Run
# Using Cloud Build (recommended)
gcloud builds submit --config deployment/cloudbuild.yaml \
  --substitutions=_GROQ_API_KEY=your_groq_key,_GOOGLE_API_KEY=your_google_key

# Or deploy directly
gcloud run deploy insightforge \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GROQ_API_KEY=your_groq_key,GOOGLE_API_KEY=your_google_key

Environment Variables Required:
GROQ_API_KEY — Primary LLM for text generation
GOOGLE_API_KEY — Fallback for ADK multi-agent traces

Documentation
| Document                  | Description                                                  |
| ------------------------- | ------------------------------------------------------------ |
| `docs/RECORDING_GUIDE.md` | Competition video production schedule                        |
| `docs/GIT_WORKFLOW.md`    | Professional Git practices and commit conventions            |
| `docs/MCP_GUIDE.md`       | Model Context Protocol architecture and integration patterns |
| `docs/WRITEUP.md`         | Kaggle submission writeup template (under 2,500 words)       |

License
This project is licensed under CC-BY 4.0, as required by the Kaggle competition rules.
Author
Ameema Rashid
GitHub: @ameema28
Project: InsightForge
Competition: Kaggle AI Agents Capstone 2026
Built for the Kaggle AI Agents: Intensive Vibe Coding Capstone 2026 sponsored by Google.