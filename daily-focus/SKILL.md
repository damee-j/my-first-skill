---
name: daily-focus
description: >
  Lark 봇이 매일 밤 10시에 DM으로 오늘 회고 + 내일 집중할 한 가지 일을 정하고,
  Lark 캘린더에 Focus Block을 자동 생성.

  트리거: "/daily-focus", "/daily-review", 또는 "오늘 집중할 일", "회고",
  "Focus Block", "캘린더 시간 확보" 같은 요청.

  외부 연동: Lark (IM + Calendar + WebSocket Event), Gemini/OpenAI/Anthropic (AI)
---

# daily-focus

매일 밤 10시, Lark 봇이 오늘의 회고를 돕고 내일 집중할 딱 한 가지 일을 정해서 Lark 캘린더에 Focus Block을 만들어주는 집중력 도우미.

## Quick Start

### 필수 환경변수

```bash
# Lark (IM + 캘린더)
LARK_APP_ID=cli_xxxxxxxxxxxx
LARK_APP_SECRET=xxxxxxxxxxxx
LARK_USER_TOKEN=  # OAuth로 자동 발급
LARK_USER_OPEN_ID=ou_xxxxxxxxxxxx

# AI APIs (스콥 분석 및 코칭)
GEMINI_API_KEY=xxxxxxxxxxxx  # Primary
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxx  # Fallback
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx  # Fallback
```

### 기본 사용법

**나이틀리 플로우 (22:00)**:
```bash
python3 nightly_flow.py
```
→ Lark DM으로 회고 질문 → 사용자 응답 → Coach 피드백 → 내일 Focus 질문 → 스콥 분석 → Focus Block 생성

## 워크플로우

### 나이틀리 워크플로우 (22:00)

#### Part A: 오늘의 회고

1. **Lark DM 발송** (자동)
   ```
   🌙 하루 고생하셨어요! 오늘의 회고 시간이에요.

   아래 4가지에 대해 자유롭게 답해주세요:
   1. 오늘 관찰한 가장 중요한 일
   2. 오늘 배운 일
   3. 오늘 실행한 일
   4. 그냥 떠오른 중요한 생각
   ```

2. **사용자 회고 답변**

3. **Coach GPT 피드백** → Lark DM 전달

#### Part B: 내일의 Focus

4. **Lark DM으로 내일 Focus 질문**
   ```
   내일(02/12 수요일) 딱 한 가지, 가장 집중하고 싶은 일은 뭐예요?
   ```

5. **사용자 답변** → 스콥 분석 → 필요시간 계산

6. **내일 캘린더 빈 시간 찾기**
   - 내일 일정 조회
   - 9:30-11:00 기존 Focus 윈도우 내 일정은 무시 (중복 OK)
   - 빈 시간에 Focus Block 분할 배치

7. **Focus Block 생성 및 요약**
   ```
   🎯 내일의 Focus
   "PRD 초안 작성"

   📏 스콥 분석
   - 예상 필요 시간: 4.0시간

   🔒 Focus Block 생성 완료!
   - 02/12(수) 10:00-11:00 (1시간)
   - 02/12(수) 14:00-17:00 (3시간)
   ```

## 스크립트 사용법

### Lark OAuth 토큰 발급

```bash
python3 scripts/lark_oauth.py
```

### Lark IM 메시지 테스트

```bash
python3 scripts/lark_im.py "테스트 메시지"
```

### WebSocket 이벤트 수신 테스트

```bash
python3 scripts/lark_event_listener.py
```
→ Lark에서 봇에게 메시지를 보내면 터미널에 표시됨. Ctrl+C로 종료.

### 캘린더 조회

```bash
python3 scripts/lark_calendar.py --list-events
```

### Focus Block 생성

```bash
python3 scripts/lark_calendar.py --create-block \
  --title "PRD 초안 작성" \
  --start "2026-02-12T10:00:00" \
  --duration 180
```

### Coach GPT 피드백

```bash
python3 scripts/coach_gpt.py --reflection "오늘 PRD 75% 완료했어요"
```

## 설정 가이드

### Lark 설정

[references/lark-setup.md](references/lark-setup.md) 참조:
- Lark 앱 생성
- Calendar API + IM 권한 설정
- OAuth 인증
- User Open ID 확인

**예상 시간**: 30분

### AI API 설정

[references/openai-setup.md](references/openai-setup.md) 참조:
- Gemini API Key 발급 (Primary)
- OpenAI/Anthropic API Key (Fallback)

**예상 시간**: 10분

## 자동화 설정 (선택)

### cron job으로 자동 실행

매일 밤 10시에 자동으로 워크플로우를 실행하려면:

```bash
crontab -e

# 아래 내용 추가
0 22 * * * cd /Users/damee/dev/my-first-skill/daily-focus && /usr/bin/python3 nightly_flow.py >> ~/daily-focus.log 2>&1
```

### GitHub Actions

`.github/workflows/daily-focus.yml` 참조. 매일 22:00 KST (13:00 UTC) 자동 실행.

## 예외 처리

### 캘린더 빈 시간 부족
→ 사용자에게 조정 옵션 제시

### 사용자 무응답
회고 무응답 → Focus 질문으로 진행. Focus 무응답 → 로그 저장 후 종료.

### API 토큰 만료
Lark DM으로 재로그인 안내 자동 발송.

## 범위

**하는 것**:
- 밤 10시 Lark DM으로 회고 질문 (관찰/배움/실행/떠오른 생각)
- Coach GPT 전문 피드백
- 내일 집중할 한 가지 일 수집
- AI 스콥 분석 및 필요시간 계산
- 내일 캘린더 빈 시간 자동 탐색 (9:30-11:00 Focus 윈도우 중복 허용)
- Focus Block 생성 (미팅 보호)

**안 하는 것**:
- 자동 우선순위 제안 (사용자가 직접 정의)
- 복잡한 프로젝트 관리 (딱 한 가지만)
- 여러 개의 작업 관리 (Only 1, not Top 3)

## 완료 기준

"매일 밤 10시에 Lark 봇이 DM으로 회고 질문을 보내고, Coach 피드백을 전달한 뒤, 내일 집중할 한 가지 일이 정해지고 필요한 시간만큼 Lark 캘린더 빈 시간에 Focus Block이 생성되는 것"
