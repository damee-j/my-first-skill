# Slack Bot 설정 가이드

이 가이드는 daily-focus 스킬에서 사용할 Slack Bot을 설정하는 방법을 안내합니다.

## 개요

- **소요 시간**: 약 20분
- **필요한 것**: Slack 워크스페이스 관리자 권한
- **권장**: 개인 Slack 워크스페이스 사용 (프라이버시 보호)

## 1. Slack App 생성

1. [Slack API](https://api.slack.com/apps) 접속
2. "Create New App" 클릭
3. "From scratch" 선택
4. App 정보 입력:
   - **App Name**: `Daily Focus Bot`
   - **Pick a workspace**: 개인 워크스페이스 선택
5. "Create App" 클릭

## 2. Bot Token Scopes 설정

1. 왼쪽 메뉴에서 **OAuth & Permissions** 클릭
2. **Scopes** 섹션에서 **Bot Token Scopes** 항목 찾기
3. "Add an OAuth Scope" 버튼 클릭하여 다음 권한 추가:
   - `chat:write` - 메시지 발송
   - `im:write` - DM 발송
   - `users:read` - 사용자 정보 읽기

## 3. Bot Token 발급

1. 같은 페이지 상단의 **OAuth Tokens for Your Workspace** 섹션으로 이동
2. "Install to Workspace" 버튼 클릭
3. 권한 요청 화면에서 "Allow" 클릭
4. **Bot User OAuth Token** 복사 (xoxb-로 시작)
   - ⚠️ 이 토큰을 안전하게 보관하세요!

## 4. User ID 확인

### 방법 1: Slack 프로필에서 확인

1. Slack 앱에서 본인 프로필 클릭
2. 프로필 화면에서 "..." (더보기) 메뉴 클릭
3. "Copy member ID" 선택
4. ID가 클립보드에 복사됨 (U로 시작, 예: U01XXXXXXXXX)

### 방법 2: API 호출로 확인

```bash
curl -H "Authorization: Bearer xoxb-your-bot-token" \
  "https://slack.com/api/users.list"
```

응답에서 본인의 이메일을 찾아 해당 user의 `id` 필드 확인

## 5. 환경변수 설정

`.env` 파일에 다음 내용 추가:

```bash
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx
SLACK_USER_ID=U01XXXXXXXXX
```

## 6. 테스트

```bash
python3 scripts/slack_dm.py "테스트 메시지"
```

성공하면:
```
✅ DM 발송 성공: 테스트 메시지...
```

Slack DM에서 "테스트 메시지"를 받았는지 확인하세요!

## 문제 해결

### "not_authed" 오류

→ `SLACK_BOT_TOKEN`이 올바르게 설정되지 않았습니다. 토큰을 다시 확인하세요.

### "channel_not_found" 오류

→ `SLACK_USER_ID`가 올바르지 않습니다. User ID를 다시 확인하세요.

### "missing_scope" 오류

→ Bot Token Scopes가 제대로 설정되지 않았습니다. 2단계로 돌아가서 권한을 추가하고 앱을 재설치하세요.

## 프라이버시 참고사항

- **개인 워크스페이스 권장**: 회사 Slack을 사용하면 관리자가 메시지를 볼 수 있습니다.
- **개인 워크스페이스 만들기**:
  1. [Slack 홈페이지](https://slack.com/get-started#/createnew) 접속
  2. 이메일로 무료 워크스페이스 생성
  3. 본인만 초대하여 사용

## 다음 단계

Slack 설정이 완료되었다면:
- [Lark 설정](lark-setup.md)
- [OpenAI 설정](openai-setup.md)
