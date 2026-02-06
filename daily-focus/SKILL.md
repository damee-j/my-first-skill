---
name: daily-focus
description: >
  Slack 봇이 매일 10시/19시에 DM으로 오늘 집중할 한 가지 일을 정하고,
  Lark 캘린더에 Focus Block을 자동 생성. 저녁에는 Coach GPT와 함께 회고.

  트리거: "/daily-focus", "/daily-review", 또는 "오늘 집중할 일", "회고",
  "Focus Block", "캘린더 시간 확보" 같은 요청.

  외부 연동: Slack (Bot API), Lark (Calendar OAuth), OpenAI (Coach GPT)
---

# daily-focus

매일 아침/저녁 자동으로 말을 걸어 오늘 집중할 딱 한 가지 일을 정하고, Lark 캘린더에 Focus Block을 만들어 미팅으로부터 보호하는 집중력 도우미.

## Quick Start

### 필수 환경변수

```bash
# Slack (개인 워크스페이스)
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx
SLACK_USER_ID=U01XXXXXXXXX

# Lark (캘린더)
LARK_APP_ID=cli_xxxxxxxxxxxx
LARK_APP_SECRET=xxxxxxxxxxxx
LARK_USER_TOKEN=  # OAuth로 자동 발급

# OpenAI (Coach GPT)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxx
COACH_GPT_ID=asst_xxxxxxxxxxxx
```

### 기본 사용법

**아침 플로우 (10:00)**:
```bash
/daily-focus
```
→ Slack DM으로 봇이 말을 걺 → 오늘 집중할 한 가지 입력 → 스콥 분석 → Lark 캘린더 빈 시간에 Focus Block 생성

**저녁 플로우 (19:00)**:
```bash
/daily-review
```
→ Slack DM으로 회고 요청 → 오늘 결과 공유 → Coach GPT 피드백 → Slack으로 전달

## 워크플로우

### 아침 워크플로우 (10:00)

1. **Slack DM 발송** (자동)
   ```
   🌅 좋은 아침이에요! 오늘 딱 한 가지, 가장 집중하고 싶은 일은 뭐예요?
   ```

2. **사용자 답변**
   ```
   신규 기능 PRD 초안 작성
   ```

3. **스콥 분석 및 필요시간 계산**
   - AI가 작업 복잡도 분석
   - 필요 시간 자동 계산 (또는 사용자 지정)

4. **Lark 캘린더 빈 시간 찾기**
   - 오늘 일정 조회
   - 미팅 사이 빈 시간 탐색
   - 필요시간만큼 분할 배치

5. **Focus Block 생성**
   ```
   🔒 Focus Block 생성 완료!
   - 10:00-11:00 (1시간) "PRD 초안 작성 - Part 1"
   - 17:00-19:00 (2시간) "PRD 초안 작성 - Part 2"
   - 총 3시간 확보

   이 시간엔 다른 미팅이 끼어들 수 없어요! 집중해봐요 💪
   ```

### 저녁 워크플로우 (19:00)

1. **Slack DM 발송** (자동)
   ```
   🌙 하루 고생하셨어요! 오늘 집중했던 'PRD 초안 작성', 어떻게 됐나요?
   ```

2. **사용자 회고**
   ```
   Part 1은 완료했고, Part 2는 50%만 했어. 피곤해서...
   ```

3. **Coach GPT 피드백**
   - 진행 상황 분석
   - 질문 중심 코칭
   - 다음 액션 제안

4. **Slack으로 피드백 전달**
   ```
   🧑‍🏫 Coach 피드백
   75% 달성은 훌륭해요! 다만 Part 2에서 속도가 느려진 이유를 살펴볼 필요가 있어요.

   질문 1: 17시 이후 집중력이 떨어진 게 단순히 피로 때문일까요,
           아니면 작업의 난이도가 예상보다 높았나요?

   제안: 내일은 가장 어려운 부분을 오전 Focus Block에 배치하는 건 어떨까요?
   ```

## 스크립트 사용법

### Lark OAuth 토큰 발급

```bash
python3 scripts/lark_oauth.py
```
브라우저가 열리고 로그인하면 `LARK_USER_TOKEN`이 자동으로 저장됩니다.

### Slack DM 테스트

```bash
python3 scripts/slack_dm.py "테스트 메시지"
```

### 캘린더 조회

```bash
python3 scripts/lark_calendar.py --list-events
```

### Focus Block 생성

```bash
python3 scripts/lark_calendar.py --create-block \
  --title "PRD 초안 작성" \
  --start "2026-02-06T10:00:00" \
  --duration 180
```

### Coach GPT 피드백

```bash
python3 scripts/coach_gpt.py --reflection "오늘 PRD 75% 완료했어요"
```

## 설정 가이드

### Slack 설정

[references/slack-setup.md](references/slack-setup.md) 참조:
- Slack Bot 생성
- Bot Token Scopes 설정 (chat:write, im:write, users:read)
- User ID 확인 방법

**예상 시간**: 20분

### Lark 설정

[references/lark-setup.md](references/lark-setup.md) 참조:
- Lark 앱 생성
- Calendar API 권한 설정
- OAuth 인증

**예상 시간**: 30분

### OpenAI Coach GPT 설정

[references/openai-setup.md](references/openai-setup.md) 참조:
- API Key 발급
- Assistant 생성
- Coach 프롬프트 설정

**예상 시간**: 10분

## 자동화 설정 (선택)

### cron job으로 자동 실행

매일 아침 10시와 저녁 7시에 자동으로 워크플로우를 실행하려면:

```bash
# crontab 편집
crontab -e

# 아래 내용 추가 (맥/리눅스)
0 10 * * * cd /Users/damee/dev/my-first-skill/daily-focus && /usr/bin/python3 morning_flow.py >> ~/daily-focus.log 2>&1
0 19 * * * cd /Users/damee/dev/my-first-skill/daily-focus && /usr/bin/python3 evening_flow.py >> ~/daily-focus.log 2>&1
```

> 💡 **Tip**:
> - Python 경로 확인: `which python3`
> - 로그는 `~/daily-focus.log`에 저장됩니다
> - 맥북이 꺼져있으면 실행되지 않으니 주의하세요
> - 경로를 본인의 실제 경로로 수정하세요

## 예외 처리

### Lark 캘린더 빈 시간 부족

```
오늘 캘린더에 빈 시간이 1시간밖에 없어요. 3시간 필요한데,
일정을 조정하거나 작업 범위를 줄일까요?
```
→ 사용자에게 조정 옵션 제시

### 사용자 무응답

1시간 후 재시도 (최대 1회)

### API 토큰 만료

```
Lark 캘린더에 접근할 수 없어요. 토큰을 다시 발급받아주세요.
python3 scripts/lark_oauth.py
```

## 프라이버시

- **Slack**: 개인 워크스페이스 사용으로 회사 관리자가 회고 내용을 볼 수 없음
- **Lark**: 캘린더만 사용 (메시징 사용 안 함)
- **로그**: 로컬에만 저장

## 범위

**하는 것**:
- 아침 10시 Slack DM으로 능동적으로 말 걸기
- 딱 한 가지 집중할 일 대화 수집
- AI 스콥 분석 및 필요시간 계산
- Lark 캘린더 빈 시간 자동 탐색
- Focus Block 생성 (미팅 보호)
- 저녁 7시 회고 요청
- Coach GPT 전문 피드백

**안 하는 것**:
- 자동 우선순위 제안 (사용자가 직접 정의)
- 복잡한 프로젝트 관리 (딱 한 가지만)
- 여러 개의 작업 관리 (Only 1, not Top 3)

## 완료 기준

"하루 동안 Slack 봇이 아침 10시/저녁 7시 2번 DM으로 말 걸어서, 오늘 집중할 한 가지 일이 정해지고 필요한 시간만큼 Lark 캘린더 빈 시간에 Focus Block이 생성되며, 저녁에 Coach GPT의 전문적인 피드백과 함께 회고가 Slack DM으로 전달되는 것"
