# Lark Bot API 연동 가이드

> 📚 **참고 문서**: Context7에서 조사한 [Lark Open Platform 공식 문서](https://open.larksuite.com/document)
>
> ⚠️ **안내**: 이 가이드는 AI가 공식 문서를 참고하여 작성했으며, 정확하지 않을 수 있습니다.
> 설정하다가 막히면 Claude Code에게 "이 부분이 안 돼요"라고 물어보면서 진행하세요!
> Claude Code가 최신 문서를 다시 찾아서 도와드릴 거예요 😊

## 목차
- [1. 사전 준비](#1-사전-준비)
- [2. Lark 봇 생성](#2-lark-봇-생성)
- [3. 권한 설정](#3-권한-설정)
- [4. 봇 설치 및 토큰 복사](#4-봇-설치-및-토큰-복사)
- [5. 그룹에 봇 초대](#5-그룹에-봇-초대)
- [6. 환경변수 설정](#6-환경변수-설정)
- [7. 테스트](#7-테스트)
- [트러블슈팅](#트러블슈팅)

---

## 1. 사전 준비

**필요한 것**:
- Lark 계정 (회사 또는 개인)
- 관리자 권한 (봇 설치를 위해 필요할 수 있음)

**예상 시간**: 20-30분

---

## 2. Lark 봇 생성

1. **Lark 개발자 콘솔 접속**
   - 브라우저에서 [https://open.larksuite.com](https://open.larksuite.com) 접속
   - Lark 계정으로 로그인

2. **앱 생성**
   - "Create App" 또는 "앱 만들기" 버튼 클릭
   - **App Name**: 봇 이름 입력 (예: "Meeting Automation Bot")
   - **Description**: 봇 설명 입력 (예: "회의록 자동 생성 및 공유")
   - "Create" 클릭

3. **App ID 확인**
   - 앱이 생성되면 **App ID**와 **App Secret**이 표시됩니다
   - 나중에 필요하니 메모해두세요

---

## 3. 권한 설정

봇이 메시지를 보내고, 캘린더를 관리하려면 권한이 필요해요.

1. **Bot 기능 활성화**
   - 왼쪽 메뉴에서 "Features" 또는 "기능" 선택
   - "Bot" 섹션에서 **Enable** 클릭

2. **권한 추가 (Scopes)**
   - "Permissions & Scopes" 또는 "권한" 탭 클릭
   - 다음 권한들을 검색해서 추가:
     - `im:message` - 메시지 발송
     - `im:message.group_at_msg` - 그룹에서 멘션
     - `im:chat` - 그룹 채팅 접근
     - `calendar:calendar` - 캘린더 읽기/쓰기
     - (daily-focus만 필요) `task:task` - 할일 생성

3. **권한 승인 요청**
   - "Submit for Approval" 또는 "승인 요청" 클릭
   - 회사 관리자가 승인해야 할 수도 있어요

---

## 4. 봇 설치 및 토큰 복사

### Install to Workspace 찾는 방법

1. **개발자 콘솔에서 앱 열기**
   - [https://open.larksuite.com](https://open.larksuite.com) 접속
   - 왼쪽 메뉴에서 방금 만든 앱 클릭

2. **Install to Workspace 버튼 찾기** (3가지 위치 중 하나):

   **위치 1**: 앱 상세 페이지 상단
   - 앱 이름 옆에 **"Install"** 또는 **"Install to Workspace"** 버튼

   **위치 2**: Version Management & Release 메뉴
   - 왼쪽 메뉴에서 **"Version Management & Release"** 또는 **"배포"** 클릭
   - **"Create a version"** 버튼 클릭
   - 버전 정보 입력 후 **"Save"**
   - **"Apply for release"** 또는 **"배포 신청"** 클릭
   - (관리자 승인 필요할 수 있음)
   - 승인 후 **"Install to Workspace"** 버튼이 활성화됨

   **위치 3**: 권한 설정 후 자동 표시
   - 3번 단계에서 권한을 추가한 후
   - 앱 페이지로 돌아가면 "Install" 버튼이 보임

3. **설치 진행**
   - **"Install to Workspace"** 클릭
   - 설치 확인 팝업에서 **"Confirm"** 또는 **"확인"** 클릭
   - (권한 승인 팝업이 뜨면 "Allow" 클릭)

### Bot Token 복사

1. **토큰 찾기** (2가지 위치 중 하나):

   **위치 1**: 설치 완료 직후
   - 설치가 완료되면 **Bot User OAuth Token**이 팝업으로 표시됩니다

   **위치 2**: Credentials & Basic Info 메뉴
   - 왼쪽 메뉴에서 **"Credentials & Basic Info"** 또는 **"인증 정보"** 클릭
   - **"App Credentials"** 섹션에서 **"Bot Token"** 찾기
   - **"Copy"** 버튼 클릭

2. **토큰 복사**
   - 토큰을 복사하세요 (보통 `t-` 또는 `cli_` 로 시작)
   - **⚠️ 주의**: 이 토큰은 비밀번호와 같아요. 절대 공유하지 마세요!

> 💡 **Tip**: 토큰이 안 보이면 앱을 다시 설치해보세요. "Uninstall" → "Install to Workspace"

---

## 5. 그룹에 봇 초대

봇이 그룹에 메시지를 보내려면, 그룹에 초대해야 해요.

1. **Lark 그룹 열기**
   - 봇을 사용할 그룹 채팅 열기

2. **봇 초대**
   - 그룹 채팅 상단의 설정 아이콘 클릭
   - "Add Members" 또는 "멤버 추가" 선택
   - 방금 만든 봇 이름 검색 (예: "Meeting Automation Bot")
   - 봇 선택 후 "Add" 클릭

3. **봇 확인**
   - 그룹에 "[봇 이름]이 추가되었습니다" 메시지가 보이면 성공!

---

## 6. 환경변수 설정

봇 토큰을 스킬에서 사용할 수 있게 설정해요.

### 방법 1: Claude Code에게 알려주기 (추천)

Claude Code와 대화창에서:

```
라크 토큰은 t-xxxxxxxxxxxxxxxxxxxxxxxx야
```

Claude Code가 자동으로 `.env` 파일에 저장해줍니다!

### 방법 2: 직접 파일 수정

1. 스킬 폴더에서 `.env` 파일 열기 (없으면 생성)
2. 다음 내용 추가:
   ```bash
   LARK_BOT_TOKEN=t-xxxxxxxxxxxxxxxxxxxxxxxx
   ```
3. 저장

---

## 7. 테스트

봇이 제대로 작동하는지 테스트해볼게요.

### 테스트 방법

1. **스킬 실행**
   ```bash
   # meeting-automation 스킬
   /meeting
   ```

2. **봇 메시지 확인**
   - Lark 그룹에 봇이 메시지를 보냈는지 확인
   - 메시지가 보이면 성공! 🎉

### 테스트가 실패하면?

아래 [트러블슈팅](#트러블슈팅) 섹션을 확인하세요.

---

## 트러블슈팅

### 문제 1: "Bot Token이 유효하지 않습니다"

**원인**: 토큰을 잘못 복사했거나, 봇이 설치되지 않았어요.

**해결 방법**:
1. Lark 개발자 콘솔에서 토큰 다시 확인
2. "Install to Workspace"를 다시 클릭
3. 새 토큰 복사 후 `.env` 파일 업데이트

### 문제 2: "권한이 없습니다 (Permission Denied)"

**원인**: 필요한 권한이 추가되지 않았어요.

**해결 방법**:
1. Lark 개발자 콘솔 → "Permissions & Scopes"
2. 필요한 권한 (위 3번 참조) 모두 추가
3. "Submit for Approval" 클릭
4. 관리자 승인 대기

### 문제 3: "그룹을 찾을 수 없습니다"

**원인**: 봇이 그룹에 초대되지 않았어요.

**해결 방법**:
1. Lark 그룹 열기
2. 그룹 설정 → "Add Members"
3. 봇 이름 검색 후 추가

### 문제 4: "메시지를 보낼 수 없습니다"

**원인**: 봇의 메시지 권한이 부족해요.

**해결 방법**:
1. Lark 개발자 콘솔 → "Permissions & Scopes"
2. `im:message` 권한 확인
3. 없으면 추가하고 "Submit for Approval"

---

## 추가 참고 자료

- [Lark Open Platform 공식 문서](https://open.larksuite.com/document)
- [Lark Bot 가이드](https://open.larksuite.com/document/client-docs/bot-v3/add-custom-bot)
- [Lark API Reference](https://open.larksuite.com/document/server-docs/api-call-guide/calling-process/api-call-process-overview)

---

**설정이 완료되면 워크샵에서 만나요!** 🚀

> ⚠️ **다시 한번**: 막히면 Claude Code에게 물어보세요! "라크 봇 설정이 안 돼요" 하고 물어보면, Claude Code가 최신 문서를 찾아서 도와드릴 거예요.
