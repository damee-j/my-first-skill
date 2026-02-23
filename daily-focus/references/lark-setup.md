# Lark 연동 가이드 (Calendar + IM)

> 📚 **참고 문서**: [Lark Open Platform 공식 문서](https://open.larksuite.com/document)
>
> ⚠️ **안내**: 이 가이드는 AI가 공식 문서를 참고하여 작성했으며, 정확하지 않을 수 있습니다.
> 설정하다가 막히면 Claude Code에게 "이 부분이 안 돼요"라고 물어보면서 진행하세요!

## 개요

- **소요 시간**: 약 30분
- **필요한 것**: Lark 계정
- **용도**: daily-focus는 Lark를 **캘린더 + IM 메시징** 모두 사용합니다

## 1. 사전 준비

**필요한 것**:
- Lark 계정 (회사 또는 개인)
- 관리자 권한 (앱 설치를 위해 필요할 수 있음)

## 2. Lark 앱 생성

1. **Lark 개발자 콘솔 접속**
   - 브라우저에서 [https://open.larksuite.com](https://open.larksuite.com) 접속
   - Lark 계정으로 로그인

2. **앱 생성**
   - "Create App" 버튼 클릭
   - **App Name**: `Daily Focus Calendar` (또는 원하는 이름)
   - **Description**: `개인 캘린더 Focus Block 관리`
   - "Create" 클릭

3. **App ID와 App Secret 복사**
   - 앱이 생성되면 **App ID**와 **App Secret**이 표시됩니다
   - 나중에 환경변수로 사용하니 메모해두세요

## 3. 권한 설정 (Calendar 전용)

1. **Permissions & Scopes 메뉴 접속**
   - 왼쪽 메뉴에서 "Permissions & Scopes" 클릭

2. **Calendar 권한 추가**
   - 다음 권한을 검색하여 추가:
     - `calendar:calendar` - 캘린더 읽기/쓰기
     - `calendar:calendar.event` - 이벤트 생성/수정/삭제

3. **IM 권한 추가** (메시징용)
   - 다음 권한을 검색하여 추가:
     - `im:message` - 메시지 읽기
     - `im:message:send_as_bot` - 봇으로 메시지 발송
     - `im:message.group_msg` - 그룹 채팅 메시지 읽기 (폴링 수신용)
     - `im:chat` - 채팅 목록 조회

4. **Bot 기능 활성화** (양방향 대화 필수)
   - 왼쪽 메뉴에서 "Features" → "Bot" 클릭
   - Bot 활성화 (이름, 설명 설정)
   - 봇이 활성화되어야 그룹 채팅에서 메시지 발송 가능

5. **OAuth 권한 타입 선택**
   - **User Access Token** 방식 사용 (개인 캘린더 접근을 위해 필수)
   - IM 발송은 **Tenant Access Token** (봇 레벨)으로 자동 처리
   - IM 수신은 **그룹 채팅 메시지 폴링** (`GET /im/v1/messages`)으로 처리

## 4. OAuth Redirect URL 설정

1. **Security Settings 메뉴 접속**
   - 왼쪽 메뉴에서 "Security Settings" 클릭

2. **Redirect URL 추가**
   - "Redirect URLs" 섹션에서 "Add" 클릭
   - 다음 URL 입력:
     ```
     http://localhost:8080/callback
     ```
   - "Save" 클릭

> 💡 **왜 필요한가요?**: OAuth 로그인 완료 후 브라우저가 이 URL로 리디렉션되어 토큰을 받습니다.

## 5. 환경변수 설정

`.env` 파일에 다음 내용 추가:

```bash
LARK_APP_ID=cli_xxxxxxxxxxxx
LARK_APP_SECRET=xxxxxxxxxxxx
LARK_USER_TOKEN=  # OAuth로 자동 발급됨
```

## 6. OAuth 토큰 발급

**자동 OAuth 플로우 실행**:

```bash
python3 scripts/lark_oauth.py
```

**실행 과정**:
1. 스크립트가 로컬 서버를 8080 포트에서 시작
2. 브라우저가 자동으로 열리고 Lark 로그인 페이지 표시
3. Lark 계정으로 로그인
4. 권한 승인 확인 (캘린더 접근 허용)
5. 리디렉션되면서 `LARK_USER_TOKEN` 자동 저장

**성공 메시지**:
```
✅ User Access Token이 발급되었습니다!
토큰이 .env 파일에 자동으로 저장되었습니다.
```

> 💡 **토큰 유효기간**: User Access Token은 일정 기간 후 만료될 수 있습니다.
> 만료 시 `lark_oauth.py`를 다시 실행하여 갱신하세요.

## 7. 테스트

### 캘린더 일정 조회

```bash
python3 scripts/lark_calendar.py --list-events
```

성공하면:
```
📅 오늘 일정 (3개):
  - 10:00-11:00 팀 미팅
  - 14:00-15:30 디자인 리뷰
  - 16:00-17:00 1:1
```

### 빈 시간 찾기

```bash
python3 scripts/lark_calendar.py --find-gaps --duration 120
```

성공하면:
```
🔍 빈 시간 (120분 이상):
  - 11:00-14:00 (180분)
  - 17:00-19:00 (120분)
```

### Focus Block 생성

```bash
python3 scripts/lark_calendar.py --create-block \
  --title "PRD 작성" \
  --start "2026-02-06T11:00:00" \
  --duration 120
```

성공하면:
```
✅ Focus Block 생성 성공: PRD 작성 (11:00-13:00)
```

Lark 캘린더에서 확인하세요!

## 트러블슈팅

### 문제 1: "Port 8080 already in use"

**원인**: 8080 포트가 이미 사용 중

**해결 방법**:
```bash
lsof -ti:8080 | xargs kill -9
python3 scripts/lark_oauth.py
```

### 문제 2: "Error code: 20029 redirect_uri request is invalid"

**원인**: Redirect URL이 개발자 콘솔에 등록되지 않음

**해결 방법**:
1. [Lark 개발자 콘솔](https://open.larksuite.com) 접속
2. 앱 선택 → "Security Settings"
3. Redirect URLs에 `http://localhost:8080/callback` 추가
4. 저장 후 다시 시도

### 문제 3: "invalid calendar_id"

**원인**: "primary" 문자열 대신 실제 캘린더 ID 필요

**해결 방법**:
- `lark_calendar.py` 스크립트는 자동으로 Primary 캘린더 ID를 조회합니다
- 수동으로 확인하려면:
  ```bash
  curl -H "Authorization: Bearer YOUR_TOKEN" \
    "https://open.larksuite.com/open-apis/calendar/v4/calendars"
  ```

### 문제 4: "token expired"

**원인**: User Access Token이 만료됨

**해결 방법**:
```bash
python3 scripts/lark_oauth.py  # 토큰 재발급
```

## 추가 참고 자료

- [Lark Calendar API 문서](https://open.larksuite.com/document/server-docs/calendar-v4/calendar/list)
- [OAuth 2.0 인증 가이드](https://open.larksuite.com/document/server-docs/authentication-management/access-token/user-access-token)
- [PKCE 보안 플로우](https://open.larksuite.com/document/server-docs/authentication-management/login-state-management/web-app-authentication-access)

## 토큰 안정성 관리

### 토큰 유효기간 문제

Lark User Access Token의 경우:
- **유효기간: 2시간** ⏰
- 만료되면 수동으로 재로그인 필요
- daily-focus 스킬이 자동 실행 중 토큰이 만료되면 실패

### 해결: Refresh Token 활용 (자동 구현됨)

daily-focus는 이미 Refresh Token 자동 갱신을 지원합니다:

**작동 방식**:
- OAuth 로그인 시 refresh token 자동 저장
- 토큰 만료 시 자동으로 갱신 (30일간 유효)
- 30일마다 한 번만 재로그인 필요

**토큰 상태 확인**:
```bash
python3 scripts/lark_token_manager.py

# 출력 예시:
# ✅ 유효한 Access Token: eyJhbGciOiJFUzI1NiIs...
# 📅 토큰 만료 정보:
#   - Access Token 만료: 2026-02-06 18:58:42
#   - Refresh Token 만료: 2026-03-08 16:58:42
```

**30일 후 재로그인 알림**:
- 스크립트가 자동으로 Lark DM으로 알림
- `python3 scripts/lark_oauth.py` 재실행

## 8. User Open ID 확인

Lark IM으로 메시지를 발송하려면 대상 사용자의 Open ID가 필요합니다.

### 방법 1: OAuth 로그인 후 API 호출

```bash
# 로그인 후 User Access Token으로 조회
curl -H "Authorization: Bearer YOUR_USER_TOKEN" \
  "https://open.larksuite.com/open-apis/authen/v1/user_info"
```

응답의 `open_id` 필드 값 (예: `ou_xxxxx`)을 `.env`의 `LARK_USER_OPEN_ID`에 설정.

### 방법 2: Lark Admin Console

관리자 권한이 있다면 Admin Console에서 사용자 프로필의 Open ID 확인 가능.

## 9. 그룹 채팅 설정 (봇 양방향 대화)

Lark 봇의 1:1 채팅은 사용자 입력이 제한될 수 있습니다.
봇과 양방향 대화를 하려면 **그룹 채팅**을 사용합니다.

### 그룹 생성 및 봇 초대

1. **Lark에서 그룹 생성**
   - Lark 앱 → 채팅 → "+" → 새 그룹 생성
   - 그룹 이름: `Daily Focus` (또는 원하는 이름)
   - 본인만 멤버로 추가

2. **봇 초대**
   - 그룹 설정(⚙️) → "봇" → "봇 추가"
   - `Daily Focus Calendar` 봇 검색 및 추가

3. **Chat ID 조회 및 저장**
   ```bash
   python3 scripts/lark_chat_discovery.py
   ```
   - 봇이 참여한 그룹 목록이 표시됨
   - 선택한 그룹의 `chat_id`가 `.env`에 자동 저장

### 테스트

```bash
python3 scripts/lark_im.py "테스트 메시지"
```

그룹 채팅에서 봇 메시지가 표시되면 성공!
그룹에서 메시지를 입력하면 봇이 폴링으로 수신합니다.

## 다음 단계

Lark 설정이 완료되었다면:
- [OpenAI 설정](openai-setup.md)
- 모든 설정이 완료되면 [SKILL.md](../SKILL.md)로 돌아가기
