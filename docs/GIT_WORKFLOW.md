# Professional Git Workflow for InsightForge

## Why This Matters

Your GitHub repo is part of your submission (20 points for Documentation) and your permanent portfolio. Recruiters and judges will read your commit history. A messy repo signals sloppy engineering.

---

## Initial Setup (Day 1)

```bash
# 1. Create repo on GitHub (already done)
#    - Name: insightforge
#    - Visibility: Public
#    - Add README: No (we have our own)
#    - Add .gitignore: No (we have our own)
#    - License: CC-BY 4.0 (required by competition rules)

# 2. Clone to your machine
git clone https://github.com/YOUR_USERNAME/insightforge.git
cd insightforge

# 3. Copy all Day 1 files into this folder
#    (agents/, tests/, docs/, requirements.txt, etc.)

# 4. Initial commit
git add .
git commit -m "feat(day1): foundation agent with security-first data tools

- Add analyze_csv tool with file validation and PII redaction
- Add generate_chart tool for matplotlib visualizations
- Add insightforge_v1 ADK agent with detailed system instructions
- Add pytest test suite covering security and data tools
- Add professional README with architecture and setup instructions"

git push origin main
```

---

## Daily Commit Pattern

Every day after coding, run these exact commands:

```bash
# Check what changed
git status

# Stage all changes
git add .

# Commit with descriptive message
git commit -m "TYPE(dayX): short description

- Specific change 1
- Specific change 2
- Specific change 3"

# Push to GitHub
git push origin main
```

---

## Commit Message Convention

Format: `type(dayN): description`

| Type | When to Use | Example |
|------|-------------|---------|
| `feat` | New feature | `feat(day2): add MCP server with stdio transport` |
| `fix` | Bug fix | `fix(day4): handle missing values in analyze_csv` |
| `test` | Adding/updating tests | `test(day5): add prompt injection test cases` |
| `docs` | Documentation only | `docs(day6): update architecture diagram` |
| `security` | Security improvements | `security(day5): add rate limiting per session` |
| `deploy` | Deployment config | `deploy(day12): add Dockerfile and Cloud Run config` |
| `refactor` | Code restructuring | `refactor(day8): split orchestrator into modules` |

### Good vs Bad Commits

**Bad:**
```bash
git commit -m "update"
git commit -m "fix bug"
git commit -m "day 3 stuff"
```

**Good:**
```bash
git commit -m "feat(day3): add session memory via MemoryBank

- Store user chart preferences across sessions
- Add memory retrieval in orchestrator agent
- Update tests for memory persistence"
```

---

## Branching Strategy (Optional but Professional)

For a 14-day solo project, `main` branch is fine. But if you want to practice enterprise workflow:

```bash
# Create feature branch
git checkout -b feature/mcp-server

# Work, commit, push
git add .
git commit -m "feat: add mcp server"
git push origin feature/mcp-server

# On GitHub, create Pull Request
# Self-review, then merge to main
```

**Do not do this if it slows you down.** Clean commits on `main` are better than messy branches.

---

## Pre-Submission Checklist (Day 14)

Run these commands before final submission:

```bash
# 1. Verify no secrets leaked
grep -r "AIza" . --include="*.py" --include="*.txt" --include="*.md"
# Should return NOTHING (your key is in .env which is gitignored)

# 2. Verify .env is not tracked
git ls-files | grep -i "\.env"
# Should return NOTHING

# 3. Run all tests
pytest -v
# All tests should pass

# 4. Check repo size
# Should be small (< 10 MB). No datasets, no videos, no images in repo.

# 5. Final commit
git add .
git commit -m "docs(final): submission-ready project

- Complete multi-agent system with ADK and MCP
- Security guardrails: validation, PII, injection protection
- Cloud Run deployment with live URL
- Professional README and architecture diagrams
- All tests passing"

git push origin main
```

---

## Portfolio Best Practices

### GitHub Repo Settings
1. **Pin this repo** to your GitHub profile (Settings → Profile → Pinned repositories)
2. **Add topics:** `google-adk`, `mcp`, `multi-agent`, `ai-agents`, `business-intelligence`, `kaggle`, `gemini`, `python`, `cloud-run`
3. **Enable Issues:** Shows you maintain the project (even if no one reports issues)
4. **Add a screenshot:** Replace `docs/architecture.png` with a real screenshot of your Streamlit app once built

### Resume Integration
**GitHub bio line:**
> "Building production-grade multi-agent systems with Google ADK. Winner/Participant: Kaggle AI Agents Capstone 2026."

**LinkedIn Featured Section:**
- Link to this repo
- Link to your Kaggle writeup
- Link to your YouTube demo

### What Recruiters See
When they open your repo, they should see:
1. Clean README with clear problem/solution
2. Professional folder structure
3. Passing tests (CI badge optional)
4. Security considerations mentioned
5. Deployment proof (live URL)
6. Consistent commit history

This signals: **"This person can ship production code, not just notebooks."**
