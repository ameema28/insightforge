# InsightForge — A Multi-Agent Analyst That Turns Messy Business Data Into Decisions

**Subtitle:** A secure, ADK-powered multi-agent Business Intelligence system that ingests real-world CSV/Excel files, scores their quality, analyzes them, and writes executive-ready reports — all through natural language.

**Track:** Agents for Business
**Team:** Ameema Rashid & Ubaidullah Farooqui

---

## The Problem

Business analysts spend an estimated 40% of their time on repetitive plumbing: fixing encodings, guessing delimiters, chasing missing values, and hand-building the same charts and summaries every week. Worse, the people who actually make decisions — managers, founders, ops leads — usually can't self-serve. They wait in a queue for an analyst, and by the time the report lands, the decision window has moved.

Two things make this expensive. First, the busywork sits before any insight is produced, so skilled people burn hours on janitorial data work. Second, the hand-off between "data" and "decision" introduces latency and translation loss. A dashboard tells you what happened; it rarely tells you what to do.

InsightForge attacks both. It is an agentic analyst that takes a raw, possibly messy file and a plain-English question, and returns a trustworthy, quality-scored analysis plus an executive summary with recommendations — in seconds, with no SQL and no manual cleanup.

## The Solution

InsightForge is a multi-agent system built on Google's Agent Development Kit (ADK). A central Orchestrator routes each request to specialist sub-agents:

- **Data Scout** ingests and profiles the file. It uses a robust loader that auto-detects encoding and delimiter, tolerates quoted/ragged rows and multi-sheet Excel, infers column types, and produces a 0-100 data-quality score across completeness, uniqueness, validity, and consistency.
- **Analyst** computes statistics and generates charts (bar/line/scatter) sized to the data.
- **Report Writer** converts findings into a concise executive brief: Key Findings, Risks, Recommendations.

Every request passes through a defense-in-depth security layer (prompt-injection detection, rate limiting, PII redaction, output sanitization, path-traversal protection). The tools are also exposed over an MCP server, so any MCP-compatible client — not just this app — can reuse InsightForge's data capabilities.

## Why This Wins for Business

The value is measurable and on the revenue/cost line, which is exactly what the Agents-for-Business track asks for:

- **Time saved:** the ingest-clean-profile-analyze-summarize loop that takes an analyst 30-60 minutes runs in seconds.
- **Trust, quantified:** the data-quality score means a manager knows how much to believe the numbers before acting — a governance feature most BI tools lack.
- **Self-serve:** a non-technical stakeholder asks a question in English and gets a decision-ready answer, removing the analyst bottleneck.

## Architecture

```
User -- Streamlit UI
          |
          v
   InsightForgeRunner        (sync bridge; live agent trace)
          |
          v
   Orchestrator Agent  ----------------- Security guardrails
     (ADK, Gemini 2.5)                   (injection / rate-limit /
          |                               PII / sanitization)
   +------+-----------+
   v      v           v
 Data   Analyst   Report Writer
 Scout    |  \        |
   |      |   charts  |
   v      v           v
  Robust loader + tools -- also exposed via -- MCP Server (stdio, JSON-RPC)
```

## Key Concepts Demonstrated

The competition requires at least three course concepts. InsightForge demonstrates five, each mapped to real code:

1. **Agent / Multi-Agent System (ADK).** `agents/orchestrator.py` composes three specialists (`data_scout.py`, `analyst.py`, `report_writer.py`) as ADK sub-agents with delegation rules. This is genuine division of labor, not one prompt wearing hats — the Orchestrator refuses to analyze and always routes.

2. **MCP Server.** `mcp_server/server.py` exposes the toolset over the Model Context Protocol via stdio/JSON-RPC (`analyze_csv_tool`, `generate_chart_tool`, `data_quality_report_tool`), each documented with a JSON schema. Any MCP client can reuse them, making InsightForge's capabilities framework-agnostic.

3. **Security Features.** `security/guardrails.py` implements four independent layers: a regex-based prompt-injection guardrail, a per-session rate limiter, an output sanitizer (blocks script/iframe injection, dangerous shell/URL patterns, credential leaks), and PII redaction (emails, phones, SSNs). Validated by a dedicated test suite.

4. **Deployability.** A `dockerfile` and `deployment/cloudbuild.yaml` package the app for Google Cloud Run. Configuration is environment-driven (`.env.example`), and no API keys are committed — verified across the codebase.

5. **Agent Skills / Clever Toolsets.** The Data Scout's `data_quality_report` tool (`agents/data_loader.py`) is the standout: a schema-agnostic ingestion engine that turns any messy file into a scored profile. This is what lets the agents handle real business data, not just the demo dataset.

## What Makes the Toolset Clever

Most course projects call `pandas.read_csv(path)` and hope. Real business files break that immediately: a European export uses semicolons, a legacy system emits Latin-1, an analyst's spreadsheet has missing values and a constant "region" column that silently poisons a group-by.

The `data_loader` module handles all of this without assuming a schema:

- Encoding detection (charset-normalizer) with UTF-8/Latin-1 fallbacks.
- Delimiter sniffing across comma/semicolon/tab/pipe.
- Tolerant parsing of quoted fields with embedded newlines and ragged rows (bad rows are skipped, not fatal).
- Chunked reading for files over 100 MB, with capped sampling so the demo stays responsive.
- Type inference that promotes text columns to numeric or datetime only when 90% of values agree.
- A weighted quality score (0.40 completeness + 0.25 uniqueness + 0.20 consistency + 0.15 validity) with a letter grade and human-readable flags for duplicates, missing data, and constant/junk columns.
- Column-synonym resolution so a question about "revenue" correctly targets an "amount" column.

This is the difference between a class assignment and something an analyst could actually point at a messy export.

## Demo Instructions

**Live app (Streamlit):**

```bash
git clone https://github.com/ameema28/insightforge.git
cd insightforge
python -m venv .venv && .venv\Scripts\activate   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # add your GROQ_API_KEY / GOOGLE_API_KEY
streamlit run app.py
```

Upload any CSV/Excel file and ask, e.g., "Summarize this and flag data-quality risks" or "Show revenue by product as a bar chart." Toggle Show execution trace to watch the multi-agent chain.

**Multi-agent UI (ADK):** `adk web`, then select the `agents` app to interact with the Orchestrator directly.

**MCP server:** `python mcp_server/server.py` starts the stdio MCP server for third-party clients.

**Tests:** `python -m pytest -v` runs 67 tests (multi-agent, MCP protocol, security, sanitizer, and the data-loader tests).

## Results & Impact

On a messy 270-row sales export (semicolon-delimited, mixed encoding, ~12% missing values, duplicate rows), the loader correctly detects the delimiter, flags the worst-missing column, catches duplicate rows, identifies constant columns, and reports a data-quality grade a human can act on — all before analysis runs. On a clean dataset it scores 100/100 and infers the date column as datetime automatically.

For a business team the impact is concrete: the weekly "clean the export, chart it, write the summary" ritual collapses into a single natural-language turn, and the quality score gives decision-makers a trust signal before they act. That is time reclaimed and risk reduced — cost and revenue, the track's exact criteria.

## Design Decisions & Trade-offs

- Groq (Llama 3.3 70B) primary with Gemini fallback keeps latency low and cost predictable for the chat path, while ADK/Gemini powers structured multi-agent reasoning.
- Direct, verified analysis over free-form LLM math for file queries: statistics come from pandas, not model guesses, which removes a whole class of hallucinated numbers.
- Additive tooling: the robust loader is exposed as a new tool alongside the original, so existing behavior is preserved and the system degrades gracefully.

## Future Work

- Multi-file joins with automatic key detection and referential-integrity checks.
- A self-correcting evaluation agent that verifies each statistic against pandas and regenerates low-confidence outputs.
- SSE transport for the MCP server and a natural-language-to-pandas query agent for ad-hoc questions.
- An HTML/PDF executive dashboard export with embedded interactive charts.

## Summary

InsightForge is a working, secure, multi-agent analyst that meets real business data where it actually lives — messy, mis-encoded, and un-cleaned — and returns quality-scored, decision-ready answers in plain English. It demonstrates five course concepts in production-quality code, is deployable to Cloud Run, and exposes its capabilities over MCP for reuse. It is not a demo of what agents could do; it is a tool a business team could start using on Monday.

*License: CC BY 4.0. Repository: https://github.com/ameema28/insightforge*
*Team: Ameema Rashid & Ubaidullah Farooqui*
