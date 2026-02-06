# daily-focus

매일 아침/저녁 자동으로 말을 걸어 오늘 집중할 딱 한 가지 일을 정하고, Lark 캘린더에 Focus Block을 만들어 미팅으로부터 보호하는 집중력 도우미.

## ✨ 최신 업데이트 (2026-02-06)

**🔐 Lark OAuth 토큰 안정성 개선**
- ✅ **자동 토큰 관리**: 만료 추적 및 자동 알림
- ✅ **장기 유효성**: 1년간 자동 갱신 (auth_exp 활용)
- ✅ **Fallback 메커니즘**: 토큰 만료 시 Slack 알림으로 안내
- ✅ **안정적인 자동 실행**: cron job이 토큰 만료로 실패하지 않음

**새로운 도구**:
- `scripts/lark_token_manager.py` - 토큰 자동 관리
- `scripts/migrate_token.py` - 기존 토큰 마이그레이션
- `scripts/lark_tenant_token.py` - Tenant Token 방식 (대안)

## 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

`.env` 파일을 생성하고 위의 환경변수들을 입력하세요.

필요한 환경변수:
- `SLACK_BOT_TOKEN` - Slack Bot 토큰
- `SLACK_CHANNEL_ID` - Slack 채널 ID (예: C0AD6RX1R3M)
- `SLACK_CHANNEL_NAME` - Slack 채널 이름 (예: daily-focus)
- `SLACK_USER_ID` - Slack 사용자 ID
- `LARK_APP_ID`, `LARK_APP_SECRET` - Lark 앱 정보
- `LARK_BOT_TOKEN` - Lark Bot 토큰
- `LARK_USER_TOKEN` - Lark 사용자 OAuth 토큰 (자동 저장됨)
- `ANTHROPIC_API_KEY` - Anthropic API 키 (스콥 분석용)
- `OPENAI_API_KEY`, `COACH_GPT_ID` - OpenAI Coach GPT

상세한 설정 가이드는 [references/](references/) 폴더를 참고하세요.

### 3. Lark OAuth 인증 (Refresh Token + Fallback)

**초기 설정** (한 번만):
```bash
# 1. Lark OAuth 로그인
python3 scripts/lark_oauth.py

# 2. 기존 토큰이 있다면 마이그레이션 (선택)
python3 scripts/migrate_token.py
```

브라우저가 열리면 Lark 계정으로 로그인하여 캘린더 접근 권한을 부여하세요.

**토큰 상태 확인**:
```bash
python3 scripts/lark_token_manager.py
```

**자동 갱신**:
- ✅ 토큰이 만료되면 자동으로 체크하고 Slack 알림
- ✅ 1년간 유효 (auth_exp 활용)
- ✅ 만료 24시간 전 Slack 경고 메시지

**재로그인 필요 시**:
- Slack에서 알림을 받으면 `python3 scripts/lark_oauth.py` 실행

### 4. 테스트 실행

**아침 워크플로우**:
```bash
python3 morning_flow.py
```

**저녁 워크플로우**:
```bash
python3 evening_flow.py
```

## 자동화 설정

매일 자동으로 실행하려면 cron job을 설정하세요:

```bash
crontab -e

# 아래 내용 추가 (경로를 본인의 실제 경로로 수정)
0 10 * * * cd /Users/damee/dev/my-first-skill/daily-focus && /usr/bin/python3 morning_flow.py >> ~/daily-focus.log 2>&1
0 19 * * * cd /Users/damee/dev/my-first-skill/daily-focus && /usr/bin/python3 evening_flow.py >> ~/daily-focus.log 2>&1
```

## 워크플로우

### 아침 (10:00)
1. Slack 채널로 인사 및 오늘 집중할 일 질문
2. 사용자 응답 대기
3. AI 스콥 분석 및 필요시간 계산
4. Lark 캘린더 빈 시간 찾기
5. Focus Block 생성
6. Slack으로 요약 전송

### 저녁 (19:00)
1. 아침에 정한 Focus 확인
2. Slack 채널로 회고 요청
3. 사용자 응답 대기
4. Coach GPT 피드백 요청
5. Slack으로 피드백 전달
6. 회고 로그 저장 (`~/.daily-focus/`)

## 문서

### 기본 문서
- [SKILL.md](SKILL.md) - 전체 스킬 문서
- [references/slack-setup.md](references/slack-setup.md) - Slack Bot 설정
- [references/lark-setup.md](references/lark-setup.md) - Lark 캘린더 설정
- [references/openai-setup.md](references/openai-setup.md) - Coach GPT 설정

### 토큰 관리 (NEW!)
- [references/lark-token-stability.md](references/lark-token-stability.md) - **토큰 안정성 가이드**
  - Refresh Token vs Tenant Token 비교
  - 자동 갱신 메커니즘
  - 문제 해결 가이드

## 라이선스

MIT
