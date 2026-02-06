# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Code 워크샵용 스킬 프로젝트 모음. 반복 업무를 자동화하는 Claude Code 스킬을 설계하고 구현한다.

## Target Users

- **clova-meeting-minutes, meeting-automation** — 제품팀(PM, 디자이너)이 주 사용자. UX 문구, 에러 메시지, 대화 시나리오 등을 비개발자가 이해하기 쉽게 작성한다. 온보딩과 설정 가이드도 기술 배경 없이 따라할 수 있어야 한다.
- **daily-focus** — Head of Product 개인 전용. 별도 온보딩 없이 본인이 직접 설정·사용하므로, 간결하고 효율적인 인터페이스를 우선한다.

## Repository Structure

이 저장소에는 3개의 독립적인 스킬 프로젝트가 있다:

- **clova-meeting-minutes/** — 클로바노트 음성기록 → 구조화된 회의록 마크다운 요약 생성 스킬. `.skill` 패키지로도 배포됨 (`clova-meeting-minutes.skill`). 설계서는 `SKILL.md` 참조.
- **meeting-automation/** — 클로바노트 → NotebookLM → Lark 공유까지 전체 파이프라인 자동화. Playwright(브라우저 자동화), NotebookLM MCP, Lark Bot API 연동. 설계서는 `meeting-automation-설계서.md` 참조.
- **daily-focus/** — Slack 봇이 매일 10시/19시에 DM으로 말을 걸어 오늘 집중할 딱 한 가지 일을 정하고, Lark 캘린더에 Focus Block을 자동 생성. 저녁에는 Coach GPT와 함께 회고. Slack (대화) + Lark (캘린더) + OpenAI (코칭) 연동. 개인 Slack 워크스페이스 사용으로 프라이버시 보호. 설계서는 `daily-focus-설계서.md` 참조.

각 스킬 폴더에는 `사전설문응답.md` (인터뷰 기록), `설계서.md` (스킬 설계), `연동가이드/` (외부 서비스 연동 가이드), `.env.example` (환경변수 템플릿)이 포함되어 있다.

## Planning Workflow

스킬 개발이나 복잡한 작업을 시작할 때는 계획을 먼저 세우고 문서화한다:

- **계획 파일 위치**: `plans/YYMMDD-스킬이름-계획.md` 형식으로 저장
  - 예: `plans/260206-daily-focus-계획.md`
- **계획 내용**: Context, Implementation Plan, Critical Files, Verification, Implementation Notes 포함
- **목적**: 작업 범위와 접근 방식을 명확히 정의하고, 향후 참조 가능하도록 보존

## External Services & MCP Servers

이 프로젝트는 두 개의 MCP 서버를 사용한다 (`.claude/settings.local.json` 참조):
- **context7** — 외부 라이브러리 문서 조회
- **notebooklm** — NotebookLM 연동 (소스 업로드, 회의록/PRD 생성)

외부 서비스 연동:
| 서비스 | 연동 방식 | 환경변수 | Context7 Library ID |
|--------|----------|---------|---------------------|
| Lark | Bot API (REST) | `LARK_BOT_TOKEN` | `/websites/open_larksuite_document` |
| NotebookLM | MCP 서버 | 자동 (Google OAuth) | `/jacob-bd/notebooklm-mcp-cli` |
| 클로바노트 | Playwright 브라우저 자동화 | 없음 (세션 파일) | `/microsoft/playwright` |

## Key Commands

```bash
# meeting-automation: Playwright 설치
cd meeting-automation && npm install playwright && npx playwright install chromium

# NotebookLM MCP 인증 (첫 사용 시)
nlm login
```

## Language

이 프로젝트의 문서와 코드 주석은 한국어로 작성한다. 사용자와의 대화도 한국어로 진행한다.
