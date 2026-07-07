# InsightForge

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Google ADK](https://img.shields.io/badge/Built%20with-Google%20ADK-orange)](https://developers.google.com/adk)
[![MCP](https://img.shields.io/badge/Protocol-MCP-purple)](https://modelcontextprotocol.io)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-green.svg)](https://creativecommons.org/licenses/by/4.0/)

> **Multi-Agent Business Intelligence System** built with Google ADK & MCP for the **Kaggle AI Agents: Intensive Vibe Coding Capstone 2026** sponsored by Google.

**Team:** Ameema Rashid & Ubaidullah Farooqui

---

## Table of Contents

- [Overview](#overview)
- [Problem Statement](#problem-statement)
- [Solution Architecture](#solution-architecture)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Security](#security)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [License](#license)
- [Team](#team)

---

## Overview

InsightForge is a production-grade multi-agent system that transforms raw business data into executive-ready reports through natural language. It demonstrates Google ADK, the Model Context Protocol (MCP), and enterprise security practices applied to real-world business intelligence.

It works on messy, real-world files — not just a clean demo dataset — by auto-detecting encoding and delimiter, scoring data quality, and reporting problems in plain language before any analysis is trusted.

---

## Problem Statement

Business analysts spend roughly 40% of their time on repetitive data tasks: fixing encodings, guessing delimiters, chasing missing values, and rebuilding the same reports every week. Non-technical managers are blocked from insights without engineering support. InsightForge automates this pipeline with a secure, multi-agent architecture that reasons about data, validates its quality, and produces actionable summaries autonomously.

---

## Solution Architecture

```
User -- Streamlit UI
          |
          v
   InsightForgeRunner        (sync bridge; live agent trace; intent routing)
          |
          v
   Orchestrator Agent  ----------------- Security guardrails
     (ADK, Gemini 2.5)                   (injection / rate-limit /
          |                               PII / output sanitization)
   +------+-----------+
   v      v           v
 Data   Analyst   Report Writer
 Scout    |  \        |
   |      |   charts  |
   v      v           v
  Robust loader + tools -- also exposed via -- MCP Server (stdio, JSON-RPC)
  (encoding/delimiter                          analyze_csv, generate_chart,
   detection, quality score)                   data_quality_report
```

The Streamlit runner routes each request by intent: data-quality/schema questions go to the robust loader (Data Scout), chart requests to the visualization path, and summaries to the analysis/report path. The full Orchestrator -> Data Scout -> Analyst -> Report Writer delegation chain runs via `adk web`.

---

## Key Features

### Real-World Data Ingestion (schema-agnostic)
- Robust `data_loader` engine (`agents/data_loader.py`) that handles messy business files:
  auto-detects **encoding** (charset-normalizer) and **delimiter** (comma/semicolon/tab/pipe),
  tolerates **quoted fields with embedded newlines** and **ragged rows**, reads **multi-sheet Excel**,
  and **chunks files over 100 MB**.
- **Data-quality score (0-100)** across completeness, uniqueness, validity, and consistency, with a
  letter grade and human-readable flags (missing data, duplicate rows, constant/junk columns).
- Automatic type inference (numeric / datetime) with a 90%-agreement threshold to avoid false positives.
- Exposed to agents and third parties as the `data_quality_report` tool (also over MCP), and surfaced
  directly in the Streamlit chat: ask *"what's the data quality of this file?"* and get a formatted
  score + schema table + flags.
- Column-synonym resolution so natural questions ("revenue by product") map to real columns ("amount").

### Multi-Agent System (Google ADK)
- **Orchestrator Agent:** central router that interprets user intent and delegates to specialists.
- **Data Scout:** loads and profiles data via `data_quality_report` and `analyze_csv`.
- **Analyst:** statistical analysis and chart generation (bar / line / scatter).
- **Report Writer:** converts findings into executive summaries (Key Findings / Risks / Recommendations).
- Full delegation chain runnable in the ADK Dev UI via `adk web`.

### MCP Server
- Standalone MCP server (`mcp_server/server.py`) exposing all data tools via the Model Context Protocol.
- Compatible with any MCP client (ADK, Claude Desktop, Cursor, custom implementations).
- Tools: `analyze_csv_tool`, `generate_chart_tool`, and `data_quality_report_tool`, over JSON-RPC / stdio.

### Security & Guardrails
- Prompt-injection detection, per-session rate limiting, PII redaction, and output sanitization
  (blocks script/iframe injection, dangerous shell/URL patterns, and credential leaks).
- Path-traversal protection and file-extension whitelisting on all file access.

---

## Tech Stack

- **Agents:** Google ADK 2.x, Gemini 2.5 Flash
- **LLM (chat path):** Groq (Llama 3.3 70B) primary, Gemini fallback
- **Protocol:** Model Context Protocol (MCP)
- **Data:** pandas, openpyxl, charset-normalizer
- **Frontend:** Streamlit
- **Viz:** matplotlib
- **Testing:** pytest (67 tests)
- **Deploy:** Docker, Google Cloud Run

---

## Project Structure

```
insightforge/
|- agents/
|  |- orchestrator.py     # ADK router + sub-agents
|  |- data_scout.py       # ingestion/profiling agent
|  |- analyst.py          # analysis + charts agent
|  |- report_writer.py    # executive summary agent
|  |- data_loader.py      # robust real-world loader + quality score
|  |- tools.py            # analyze_csv, generate_chart, data_quality_report
|  |- runner.py           # Streamlit sync bridge + intent routing
|  |- memory.py           # session persistence
|- mcp_server/server.py   # MCP server (3 tools)
|- security/guardrails.py # injection / rate-limit / sanitize / PII
|- tests/                 # 67 pytest cases
|- docs/                  # WRITEUP, VIDEO_SCRIPT, etc.
|- app.py                 # Streamlit frontend
|- dockerfile
|- deployment/cloudbuild.yaml
|- LICENSE                # CC BY 4.0
|- sample_sales.csv
```

---

## Getting Started

```bash
git clone https://github.com/ameema28/insightforge.git
cd insightforge
python -m venv .venv
# Windows: .venv\Scripts\activate    |    macOS/Linux: source .venv/bin/activate
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env               # add your GROQ_API_KEY / GOOGLE_API_KEY
streamlit run app.py
```

---

## Usage

**Streamlit app:** upload a CSV/Excel file, then try:
- `what's the data quality of this file?` -> Data Scout quality report (score + schema + flags)
- `bar chart of revenue by product` -> chart
- `summarize this file for a manager` -> executive summary

**Multi-agent Dev UI:** `adk web`, select the `agents` app, then ask
`analyze sample_sales.csv and write an executive summary` to watch the full delegation chain.

**MCP server:** `python mcp_server/server.py` starts the stdio MCP server for third-party clients.

---

## Security

Every input passes through a defense-in-depth layer: prompt-injection detection, per-session rate
limiting, PII redaction (emails/phones/SSNs), and output sanitization (script/iframe injection,
dangerous commands, credential leaks). File access is whitelisted by extension and protected against
path traversal. No API keys are stored in code; configuration is environment-driven.

---

## Testing

```bash
python -m pytest -v
```

67 tests pass, covering security guardrails, data tools, MCP protocol compliance, agent
initialization, the multi-agent hierarchy, and the robust data loader.

---

## Deployment

```bash
# Cloud Build
gcloud builds submit --config deployment/cloudbuild.yaml

# Or deploy directly
gcloud run deploy insightforge --source . --region us-central1 --allow-unauthenticated \
  --set-env-vars GROQ_API_KEY=your_groq_key,GOOGLE_API_KEY=your_google_key
```

Environment variables: `GROQ_API_KEY` (primary LLM), `GOOGLE_API_KEY` (ADK / Gemini).

---

## Documentation

| Document                  | Description                                            |
| ------------------------- | ------------------------------------------------------ |
| `docs/WRITEUP.md`         | Kaggle submission writeup (under 2,500 words)          |

---

## License

Licensed under **CC BY 4.0**, as required by the Kaggle competition rules. See `LICENSE`.

---

## Team

- **Ameema Rashid** — [@ameema28](https://github.com/ameema28)
- **Ubaidullah Farooqui**

Built for the **Kaggle AI Agents: Intensive Vibe Coding Capstone 2026** sponsored by Google.
