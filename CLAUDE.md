# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Claude Code Skills workshop project for automating repetitive product management workflows. It contains three skills, primarily documented in Korean. The project is currently in the **design/template phase** — design documents and integration guides are complete, but implementation code has not yet been written.

## Skills

### 1. clova-meeting-minutes
Summarizes Clova Note voice recordings into structured markdown meeting notes. Read-only skill using Claude's Read tool — no external API calls. Skill spec lives in `clova-meeting-minutes/SKILL.md`.

### 2. meeting-automation
Full meeting workflow: download Clova Note (Playwright browser automation) → upload to NotebookLM (MCP) → generate meeting minutes or PRD → share to Lark (Bot API). Most complex skill with three external service integrations.

### 3. daily-focus
Lark bot-driven daily workflow with morning goal-setting (Top 3 priorities → calendar events + tasks) and evening reflection. Uses cron scheduling for 9 AM / 6 PM triggers.

## Commands

```bash
# meeting-automation setup
cd meeting-automation && npm install
npx playwright install chromium

# Environment setup (both meeting-automation and daily-focus)
cp meeting-automation/.env.example meeting-automation/.env
cp daily-focus/.env.example daily-focus/.env
# Edit .env files to add LARK_BOT_TOKEN

# sparkling_star.py (decorative utility, requires pillow, imageio, numpy)
pip install pillow imageio numpy
python3 sparkling_star.py
```

There is no test suite, linter, or build system configured yet.

## Architecture

Each skill is a self-contained directory with:
- A design document (`*-설계서.md`) specifying workflows, integrations, and acceptance criteria
- Integration guides (`연동가이드/`) with step-by-step API setup instructions
- Pre-workshop interview notes (`사전설문응답.md`) describing the problem context
- Environment templates (`.env.example`) for API tokens

External integrations:
| Service | Skills | Auth |
|---------|--------|------|
| Lark Bot API | meeting-automation, daily-focus | OAuth token in `.env` |
| NotebookLM | meeting-automation | Google OAuth via MCP server |
| Clova Note | meeting-automation | Browser session via Playwright |

## Key Design Documents

- `meeting-automation/meeting-automation-설계서.md` — complete workflow spec, test checklist, done criteria
- `daily-focus/daily-focus-설계서.md` — morning/evening flow specs, Lark integration details
- `clova-meeting-minutes/SKILL.md` — skill definition, output format, parsing rules
- `clova-meeting-minutes/references/clovanote-format.md` — Clova Note text format specification
