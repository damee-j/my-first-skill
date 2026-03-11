# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lark 봇이 매일 밤 10시에 그룹 채팅으로 오늘의 회고(관찰/배움/실행/떠오른 생각)를 돕고, 내일 집중할 한 가지 일을 정해서 Lark 캘린더에 Focus Block을 자동 생성하는 개인 생산성 도구. Head of Product 1인 전용.

## Architecture

단일 나이틀리 플로우가 22:00 KST에 실행된다:

**nightly_flow.py** (22:00 KST):
- Part A 회고: Lark 회고 질문 4가지 → 사용자 응답 대기(15분) → 기록 저장
- Part B 내일 Focus: Lark 질문 → 사용자 응답 대기(15분) → 스콥 분석(키워드 휴리스틱) → **내일** 캘린더 빈 시간 탐색 → Focus Block 생성 → 요약 발송
- 로그 저장: `~/.daily-focus/{날짜}.json`
- Part A 타임아웃 시 Part B로 넘어감 (graceful degradation)

`scripts/` 디렉토리의 모듈들은 `sys.path.insert`로 로드된다 (패키지가 아님):
- **lark_im.py** — `send_message()`. Tenant Access Token으로 그룹 채팅에 메시지 발송. `**bold**` 마크다운 자동 제거 (Lark IM 미지원)
- **lark_event_listener.py** — `start_listener()`, `wait_for_message()`, `clear_queue()`. 그룹 채팅 메시지 폴링으로 사용자 응답 수신
- **scope_analyzer.py** — `analyze_scope()`. 키워드 휴리스틱으로 작업 시간 추정 (LLM API 키 설정 시 AI 분석도 가능)
- **lark_calendar.py** — 일정 조회(`/events/instance_view`), 빈 시간 탐색, Focus Block CRUD
- **lark_token_manager.py** — User Access/Refresh 토큰 자동 갱신 (캘린더용). 캐시: `~/.daily-focus/lark_tokens.json`
- **lark_tenant_token.py** — Tenant Access Token 자동 발급/갱신 (IM용). 캐시: `~/.daily-focus/tenant_token.json`
- **lark_oauth.py** — PKCE OAuth 2.0 플로우. 로컬 HTTP 서버(localhost:8080)로 callback 수신

## Key Commands

```bash
# 의존성 설치
pip install -r requirements.txt

# 나이틀리 플로우 실행
python3 nightly_flow.py

# Lark OAuth 로그인 (토큰 만료 시)
python3 scripts/lark_oauth.py

# 개별 스크립트 테스트
python3 scripts/lark_im.py "테스트 메시지"
python3 scripts/lark_event_listener.py  # 그룹 채팅 폴링 수신 테스트
python3 scripts/lark_calendar.py --list-events
python3 scripts/lark_calendar.py --find-gaps --duration 180
python3 scripts/lark_calendar.py --create-block --title "작업명" --start "2026-02-12T10:00:00" --duration 180
python3 scripts/scope_analyzer.py "PRD 초안 작성"
```

## Two-Token System

Lark는 용도별로 다른 토큰을 사용한다:

| 토큰 | 용도 | 발급 | 만료 | 갱신 |
|------|------|------|------|------|
| **Tenant Access Token** | IM 메시지 발송/수신 | App ID + Secret | ~2시간 | 자동 (무한) |
| **User Access Token** | 캘린더 CRUD | OAuth PKCE | ~2시간 | Refresh Token (~7일) |

토큰 만료 시 `check_lark_token()`이 Lark 메시지로 재로그인 안내. 캘린더 불가 시에도 IM은 정상 동작.

## Environment Variables

`.env` 파일에 설정 (템플릿: `assets/.env.example`):

| 변수 | 용도 |
|------|------|
| `LARK_APP_ID`, `LARK_APP_SECRET` | Lark 앱 인증 (Tenant Token 발급) |
| `LARK_USER_TOKEN` | Lark User Access Token (캘린더, 자동 갱신) |
| `LARK_REFRESH_TOKEN` | Lark Refresh Token (User Token 자동 갱신용) |
| `LARK_USER_OPEN_ID` | Lark 사용자 Open ID (ou_xxxxx) |
| `LARK_CHAT_ID` | Lark 그룹 채팅 ID (봇 양방향 대화) |
| `GEMINI_API_KEY` | (선택) 스콥 분석 AI 모드 |
| `OPENAI_API_KEY` | (선택) 스콥 분석 AI 폴백 |
| `ANTHROPIC_API_KEY` | (선택) 스콥 분석 AI 폴백 |

## Known Quirks & Gotchas

**캘린더 반복 일정**: Lark `/events` 엔드포인트는 반복 일정의 **최초 생성일** 타임스탬프를 반환한다 (예: 2025-12-03에 만든 주간 반복이면 2026-02-13 조회해도 start_time이 2025-12-03). 반드시 **`/events/instance_view`** 엔드포인트를 사용해야 실제 발생일의 타임스탬프를 얻는다.

**Lark 메시지 타입**: 그룹 채팅에서 사용자가 보내는 메시지는 `msg_type == "text"`가 아니라 **`"post"`** (리치 텍스트)로 도착한다. `_extract_text_from_post()`로 `{content: [[{tag: "text", text: "..."}]]}` 구조에서 텍스트를 추출해야 한다.

**캘린더 빈 시간 탐색 필터링** (`find_free_slots_for_date`):
- 근무시간: 10:00-19:00, 점심: 11:00-12:00 (하드코딩)
- 9:30-11:00 Focus 윈도우 내 기존 일정은 무시 (Focus 전용 시간대)
- 8시간 이상 이벤트 무시 (재택/WFH 등 배경 일정)
- `free_busy_status == "free"` 일정 무시

**사용자 입력 포맷**: `"작업명 | 시간"` (예: `"PRD 초안 작성 | 4시간"`). `|` 없으면 키워드 휴리스틱으로 시간 추정.

**Lark international**: WebSocket 이벤트 구독 미지원. 폴링(5초 간격) 방식으로 메시지 수신.

## External Service Details

**Lark IM API**: `open.larksuite.com/open-apis/im/v1/`. 발송: `POST /messages?receive_id_type=chat_id`. 수신: `GET /messages?container_id_type=chat&start_time={baseline}` 폴링. 봇 메시지 필터: `sender_type == "app"` 제외.

**Lark Calendar API**: `open.larksuite.com/open-apis/calendar/v4/`. `type == "primary"` 캘린더만 사용. Focus Block: `🔒` 제목 접두사, `visibility=private`, `free_busy_status=busy`.

**Gemini API** (선택): `generativelanguage.googleapis.com`. scope_analyzer에서 AI 분석 모드 시 `google-genai` SDK로 structured JSON output (`gemini-2.0-flash`). API 키 없으면 키워드 휴리스틱으로 동작.

## Data Flow

로그 파일 위치: `~/.daily-focus/`
- `{YYYY-MM-DD}.json` — 회고(reflection) + 내일 Focus(tomorrow_focus) 통합 로그
- `lark_tokens.json` — Lark User Token 캐시 (access_token, refresh_token, expires_at)
- `tenant_token.json` — Lark Tenant Token 캐시

## CI/CD

GitHub Actions 워크플로우: `.github/workflows/daily-focus.yml`
- 스케줄: 12:00 UTC (21:00 KST) 단일 cron
- 수동 실행: workflow_dispatch
- Secrets: `LARK_APP_ID`, `LARK_APP_SECRET`, `LARK_USER_TOKEN`, `LARK_REFRESH_TOKEN`, `LARK_USER_OPEN_ID`, `LARK_CHAT_ID`
- 제약: GitHub Actions에서는 OAuth 브라우저 플로우 불가 → User Token 만료 시 로컬에서 `lark_oauth.py` 실행 후 Secrets 수동 업데이트 필요

## Language

이 프로젝트의 문서와 코드 주석은 한국어로 작성한다. 사용자와의 대화도 한국어로 진행한다.
