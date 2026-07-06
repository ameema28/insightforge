# InsightForge — Drop-in Patch (apply into your repo root)

Copy these files over your existing repo, preserving paths. All changes are
additive or bug-fixes; nothing existing is removed except the broken filename below.

## NEW files
- agents/data_loader.py        Robust real-world loader + 0-100 quality score
- tests/test_data_loader.py    25 tests for the loader
- security/__init__.py         Proper package init (replaces the broken one below)
- LICENSE                       CC-BY 4.0 (required by competition rules)
- docs/WRITEUP.md              Kaggle writeup, 1,263 words (limit 2,500)
- docs/VIDEO_SCRIPT.md         5-minute demo script with timestamps

## MODIFIED files (safe, additive)
- agents/tools.py              + data_quality_report() tool (analyze_csv untouched)
- agents/data_scout.py         Data Scout now calls data_quality_report first
- mcp_server/server.py         + data_quality_report_tool MCP endpoint
- security/guardrails.py       Fixed XSS gap: now flags <script>/<iframe> tags
- README.md                    + "Real-World Data Ingestion" feature section

## DELETE this stray file from your repo (broken name; replaced by __init__.py)
    security/_init.py_

## Verify after applying
    pytest -v
