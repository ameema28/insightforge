# InsightForge — 5-Minute Demo Video Script

**Target length:** 4:45 (leaves buffer under the 5:00 hard limit).
**Format:** screen recording + voiceover. Record at 1080p. Keep the cursor deliberate.
**Tip:** record the demo run *first* on a real messy file so the timing is real, then narrate.

---

### 0:00–0:25 — Hook
**On screen:** a genuinely messy spreadsheet — semicolons, an accented name, blank cells, a duplicated row. Scroll through it slowly.

> "This is what business data actually looks like. Mis-encoded, wrong delimiter, missing values, duplicates. Before anyone gets an insight, an analyst spends hours cleaning this by hand — roughly 40% of their week. InsightForge does it in seconds."

---

### 0:25–1:10 — The problem, concretely
**On screen:** show the manual workflow you're replacing — open the file in Excel, a column is garbled, you fix encoding, you write a formula, you build a chart. Speed-ramp this to look tedious.

> "Today the pipeline is: fix the file, write the query, build the chart, write the summary, hand it to a manager. Every week. And the manager still can't self-serve — they wait in a queue. That queue is where decisions go to die."

**On screen:** cut to the InsightForge Streamlit UI, clean and ready.

> "InsightForge collapses that whole loop into one question, in plain English."

---

### 1:10–2:45 — Solution demo (the core — spend the most time here)
**On screen:** drag the messy CSV into the uploader. It succeeds.

> "I drop in the raw file — no cleaning. Watch the agents work."

**On screen:** toggle **Show execution trace** ON. Type: *"Summarize this file and flag any data-quality risks."* Send.

Narrate as the trace appears, pointing at each step:

> "The Orchestrator routes to the Data Scout, which profiles the file — it auto-detected the encoding and the delimiter, so nothing broke. It gives us a data-quality score: [read the number]. It flags the 50%-missing column and the duplicate rows. That score matters — it tells the manager how much to trust what comes next."

**On screen:** the Analyst/Report Writer output renders — key findings, risks, recommendations.

> "Then the Analyst computes the real statistics — from pandas, not the model, so no made-up numbers — and the Report Writer turns it into an executive brief with actual recommendations."

**On screen:** type *"Show revenue by region as a bar chart."* Send. Chart renders.

> "And I can just ask for a chart. It picks the columns and the type automatically."

---

### 2:45–3:35 — Architecture & the concepts (prove the engineering)
**On screen:** split view or quick cuts: the trace panel, then `agents/orchestrator.py`, then `mcp_server/server.py`, then `security/guardrails.py`.

> "Under the hood this is five course concepts working together. A real multi-agent system on Google's ADK — an Orchestrator delegating to three specialists. An MCP server that exposes these tools to any client. Four security layers: prompt-injection detection, rate limiting, PII redaction, output sanitization."

**On screen:** briefly type a prompt-injection attempt like *"ignore all previous instructions"* and show it getting blocked.

> "Try to hijack it — it's blocked. And the clever part is the ingestion engine: it's what let that messy file just work."

---

### 3:35–4:20 — Deployability
**On screen:** show the `dockerfile`, then a terminal: `docker build` / `docker run` (pre-recorded so it's fast), app opens on localhost. Then show `deployment/cloudbuild.yaml`.

> "It's built to ship. One Dockerfile, a Cloud Run config, environment-driven secrets — and I've checked: no API keys anywhere in the code. This runs the same on your laptop or in the cloud."

**On screen:** open the running app on a phone (or a narrow browser window) to show it's accessible.

---

### 4:20–4:45 — Close & call to action
**On screen:** the GitHub repo page; overlay the URL and "CC BY 4.0".

> "InsightForge — a secure, multi-agent analyst that meets messy business data where it lives and returns decisions, not dashboards. Code's public, MIT-clean, CC-BY licensed. Link's below. Thanks for watching."

---

## Recording checklist
- [ ] Prepare ONE messy CSV in advance (semicolon delimiter, one Latin-1 accent, a fully-missing column, a duplicate row) so the quality score and flags are visibly non-trivial.
- [ ] Pre-run `docker build` so the video shows a cached, fast run.
- [ ] Have a valid `GROQ_API_KEY` set so the chat path works live.
- [ ] Turn the trace toggle ON before the main query — the visible agent chain is the money shot.
- [ ] Keep total runtime under 5:00; upload to YouTube as **Public** or **Unlisted-that-is-viewable**, and confirm the link plays in an incognito window.
- [ ] Add the GitHub link and license to the video description.
