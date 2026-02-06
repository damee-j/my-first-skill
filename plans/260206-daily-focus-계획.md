# Plan: daily-focus 스킬 생성

## Context

사용자가 daily-focus 스킬을 만들고자 합니다. 이 스킬은 매일 아침/저녁에 자동으로 작동하여:
- **아침 10시**: Slack DM으로 오늘 집중할 한 가지 일을 묻고, 스콥을 분석하여 Lark 캘린더에 Focus Block 생성
- **저녁 7시**: 회고를 요청하고 Coach GPT의 피드백을 Slack DM으로 전달

현재 `/Users/damee/dev/my-first-skill/daily-focus/` 디렉토리가 이미 존재하며:
- 설계서 (`daily-focus-설계서.md`)
- 일부 Python 스크립트 (Lark OAuth 관련)
- 환경변수 템플릿 (`.env.example`)
- 연동 가이드 (`연동가이드/lark.md`)

가 포함되어 있습니다.

**목표**: 기존 파일들을 skill-creator 구조에 맞춰 재구성하고, 누락된 스크립트를 추가하여 완전한 스킬로 패키징

## Implementation Plan

### Phase 1: 스킬 디렉토리 구조 생성

기존 daily-focus 폴더를 skill-creator 표준 구조로 재구성:

```
daily-focus/
├── SKILL.md (새로 생성)
├── scripts/
│   ├── lark_oauth.py (기존 파일 이동)
│   ├── lark_calendar.py (새로 생성)
│   ├── slack_dm.py (새로 생성)
│   ├── coach_gpt.py (새로 생성)
│   └── scope_analyzer.py (새로 생성)
├── references/
│   ├── lark-setup.md (기존 연동가이드/lark.md 이동)
│   ├── slack-setup.md (새로 생성)
│   └── openai-setup.md (새로 생성)
└── assets/
    ├── .env.example (기존 파일 이동)
    └── coach-prompt.txt (새로 생성)
```

**작업**:
1. `scripts/`, `references/`, `assets/` 디렉토리 생성
2. 기존 파일들을 적절한 위치로 이동

### Phase 2: SKILL.md 작성

skill-creator 가이드라인에 따라 SKILL.md 작성:

**Frontmatter (YAML)**:
```yaml
---
name: daily-focus
description: >
  Slack 봇이 매일 10시/19시에 DM으로 오늘 집중할 한 가지 일을 정하고,
  Lark 캘린더에 Focus Block을 자동 생성. 저녁에는 Coach GPT와 함께 회고.

  트리거: "/daily-focus", "/daily-review", 또는 "오늘 집중할 일", "회고",
  "Focus Block", "캘린더 시간 확보" 같은 요청.

  외부 연동: Slack (Bot API), Lark (Calendar OAuth), OpenAI (Coach GPT)
---
```

**Body (핵심 워크플로우만 포함, 500줄 이하)**:
- Quick Start (핵심 사용법)
- 아침 워크플로우 (간결한 단계)
- 저녁 워크플로우 (간결한 단계)
- 스크립트 사용법 (scripts/ 참조)
- 설정 가이드 (references/ 참조)

상세 내용은 references/로 분리하여 Progressive Disclosure 원칙 준수.

### Phase 3: 스크립트 구현

#### 3.1 기존 스크립트 정리
- `lark_oauth.py`: 이미 구현됨. scripts/로 이동하고 독립 실행 가능하게 수정

#### 3.2 새 스크립트 생성

**`scripts/slack_dm.py`**:
```python
#!/usr/bin/env python3
"""Slack DM 발송"""
# SLACK_BOT_TOKEN, SLACK_USER_ID 사용
# 기능: DM 발송, 메시지 수신 대기
```

**`scripts/lark_calendar.py`**:
```python
#!/usr/bin/env python3
"""Lark 캘린더 조회 및 Focus Block 생성"""
# LARK_USER_TOKEN 사용 (lark_oauth.py로 발급)
# 기능:
# - 오늘 일정 조회
# - 빈 시간 찾기
# - Focus Block 생성
```

**`scripts/coach_gpt.py`**:
```python
#!/usr/bin/env python3
"""Coach GPT 피드백 요청"""
# OPENAI_API_KEY, COACH_GPT_ID 사용
# 기능: 회고 내용 → Coach GPT → 피드백 반환
```

**`scripts/scope_analyzer.py`**:
```python
#!/usr/bin/env python3
"""작업 스콥 분석 및 필요시간 계산"""
# Claude API 또는 로컬 LLM 사용
# 기능: 작업 설명 → 복잡도 분석 → 필요시간 계산
```

### Phase 4: References 작성

#### `references/slack-setup.md`
Slack Bot 생성 및 Token 발급 가이드:
- Slack API 앱 생성
- Bot Token Scopes 추가 (chat:write, im:write, users:read)
- User ID 확인 방법

#### `references/openai-setup.md`
OpenAI Coach GPT 설정 가이드:
- API Key 발급
- Assistant 생성 방법
- Coach 프롬프트 예시

#### `references/lark-setup.md`
기존 `연동가이드/lark.md` 파일을 재구성하여 캘린더 중심으로 수정

### Phase 5: Assets 준비

#### `assets/.env.example`
기존 파일 업데이트:
```bash
# Slack
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx
SLACK_USER_ID=U01XXXXXXXXX

# Lark
LARK_APP_ID=cli_a90ee729a4389eed
LARK_APP_SECRET=uW053LW5nhMOBloQoAgQze5aLFC54Syq
LARK_USER_TOKEN=  # OAuth로 자동 발급

# OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxx
COACH_GPT_ID=asst_xxxxxxxxxxxx
```

#### `assets/coach-prompt.txt`
설계서의 Coach GPT 프롬프트 저장

### Phase 6: 테스트 및 패키징

1. **스크립트 테스트**:
   - `lark_oauth.py` 실행 → 토큰 발급 확인
   - `slack_dm.py` 실행 → DM 발송 확인
   - `lark_calendar.py` 실행 → 캘린더 조회 확인

2. **패키징**:
```bash
python3 /Users/damee/.claude/skills/skill-creator/scripts/package_skill.py \
  /Users/damee/dev/my-first-skill/daily-focus
```

3. **validation 자동 실행**:
   - YAML frontmatter 검증
   - 파일 구조 검증
   - Description 완성도 검증

## Critical Files

### 수정할 파일:
- `/Users/damee/dev/my-first-skill/daily-focus/` - 전체 재구성
- 새로 생성: `SKILL.md`
- 새로 생성: `scripts/slack_dm.py`, `scripts/lark_calendar.py`, `scripts/coach_gpt.py`, `scripts/scope_analyzer.py`
- 새로 생성: `references/slack-setup.md`, `references/openai-setup.md`
- 수정: `references/lark-setup.md` (기존 연동가이드 기반)

### 이동/재사용할 파일:
- `lark_oauth.py` → `scripts/lark_oauth.py`
- `.env.example` → `assets/.env.example`
- `연동가이드/lark.md` → `references/lark-setup.md`

### 삭제할 파일:
- `daily-focus-설계서.md` (내용은 SKILL.md와 references/로 분산)
- `사전설문응답.md` (스킬에 불필요)
- `get_calendar_events.py`, `show_calendar.py` (lark_calendar.py로 통합)

## Verification

### 테스트 방법:
1. **환경 설정**:
   ```bash
   cd /Users/damee/dev/my-first-skill/daily-focus
   cp assets/.env.example .env
   # .env 파일 편집하여 실제 토큰 입력
   ```

2. **Lark OAuth 테스트**:
   ```bash
   python3 scripts/lark_oauth.py
   # 브라우저 열림 → 로그인 → 토큰 발급 확인
   ```

3. **Slack DM 테스트**:
   ```bash
   python3 scripts/slack_dm.py "테스트 메시지"
   # Slack DM 수신 확인
   ```

4. **캘린더 조회 테스트**:
   ```bash
   python3 scripts/lark_calendar.py --list-events
   # 오늘 일정 출력 확인
   ```

5. **스킬 패키징**:
   ```bash
   python3 /Users/damee/.claude/skills/skill-creator/scripts/package_skill.py \
     /Users/damee/dev/my-first-skill/daily-focus
   # daily-focus.skill 파일 생성 확인
   ```

### 성공 기준:
- [ ] SKILL.md가 500줄 이하로 간결
- [ ] 모든 스크립트가 독립 실행 가능
- [ ] package_skill.py validation 통과
- [ ] daily-focus.skill 파일 생성 성공
- [ ] Claude Code에서 스킬 로드 후 "/daily-focus" 트리거 동작

## Implementation Notes

### 주의사항:
1. **Progressive Disclosure**: SKILL.md는 핵심만, 상세 내용은 references/
2. **스크립트 독립성**: 각 스크립트는 독립 실행 가능해야 함
3. **환경변수**: .env 파일로 모든 credentials 관리
4. **프라이버시**: Slack 개인 워크스페이스 사용 강조

### 기존 파일 재사용:
- `lark_oauth.py`: 이미 잘 구현됨. 그대로 사용
- `.env.example`: Slack, OpenAI 환경변수 추가
- `연동가이드/lark.md`: 캘린더 중심으로 간소화

### 새로 구현 필요:
- Slack Bot API 연동 (python-slack-sdk 사용)
- OpenAI Assistant API 연동
- 작업 스콥 분석 로직
- 캘린더 빈 시간 찾기 알고리즘
