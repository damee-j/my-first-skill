# NotebookLM MCP 연동 가이드

> 📚 **참고 문서**: Context7에서 조사한 [NotebookLM MCP CLI](https://context7.com/jacob-bd/notebooklm-mcp-cli)
>
> ⚠️ **안내**: 이 가이드는 AI가 공식 문서를 참고하여 작성했으며, 정확하지 않을 수 있습니다.
> 설정하다가 막히면 Claude Code에게 "이 부분이 안 돼요"라고 물어보면서 진행하세요!
> Claude Code가 최신 문서를 다시 찾아서 도와드릴 거예요 😊

## 목차
- [1. 사전 준비](#1-사전-준비)
- [2. MCP 서버 설정](#2-mcp-서버-설정)
- [3. Claude Code 재시작](#3-claude-code-재시작)
- [4. 인증 (Google 로그인)](#4-인증-google-로그인)
- [5. 테스트](#5-테스트)
- [트러블슈팅](#트러블슈팅)

---

## 1. 사전 준비

**필요한 것**:
- Google 계정 (NotebookLM 접근 가능한 계정)
- Node.js 설치 (보통 이미 설치되어 있음)

**예상 시간**: 10-15분

**좋은 소식**: NotebookLM MCP는 별도의 API 키나 토큰이 필요 없어요! Google 로그인만 하면 됩니다.

---

## 2. MCP 서버 설정

NotebookLM을 Claude Code에서 사용하려면 MCP 서버를 추가해야 해요.

### 방법 1: Claude Code에게 부탁하기 (추천)

Claude Code와 대화창에서:

```
노트북LM MCP 서버 설정해줘
```

Claude Code가 자동으로 `~/.mcp.json` 파일에 추가해줍니다!

### 방법 2: 직접 설정하기

1. **터미널 열기**
   - macOS: `Cmd + Space` → "Terminal" 입력
   - Windows: `Win + R` → "cmd" 입력

2. **MCP 설정 파일 열기**
   ```bash
   nano ~/.mcp.json
   ```
   (또는 VSCode로 열기: `code ~/.mcp.json`)

3. **설정 추가**
   파일에 다음 내용 추가:
   ```json
   {
     "mcpServers": {
       "notebooklm": {
         "command": "npx",
         "args": ["-y", "notebooklm-mcp-cli"]
       }
     }
   }
   ```

4. **저장 후 닫기**
   - nano: `Ctrl + X` → `Y` → `Enter`
   - VSCode: `Cmd + S` (저장) → 닫기

---

## 3. Claude Code 재시작

MCP 설정은 Claude Code를 재시작해야 적용돼요.

1. **Claude Code 종료**
   - macOS: `Cmd + Q`
   - Windows: 창 닫기

2. **Claude Code 다시 열기**

3. **MCP 서버 로딩 확인**
   - Claude Code 시작 시 "Loading MCP servers..." 메시지가 잠깐 보이면 성공!

---

## 4. 인증 (Google 로그인)

처음 NotebookLM을 사용할 때, Google 로그인이 필요해요.

### 자동 인증 (브라우저 팝업)

1. **스킬 실행**
   ```bash
   /meeting
   ```

2. **브라우저 자동 열림**
   - Chrome이 자동으로 열리고 Google 로그인 페이지가 나타나요

3. **Google 로그인**
   - NotebookLM에 접근 가능한 Google 계정으로 로그인
   - "Allow" 또는 "허용" 클릭

4. **인증 완료**
   - 브라우저 창이 자동으로 닫히고, 스킬이 이어서 실행돼요

### 수동 인증 (터미널)

브라우저가 자동으로 안 열리면:

1. **터미널에서 인증**
   ```bash
   npx notebooklm-mcp-cli login
   ```

2. **URL 복사**
   - 터미널에 표시된 URL을 브라우저에 붙여넣기

3. **Google 로그인**
   - 위와 동일하게 진행

4. **인증 코드 복사**
   - 로그인 후 표시되는 코드를 터미널에 붙여넣기

---

## 5. 테스트

NotebookLM이 제대로 작동하는지 테스트해볼게요.

### 테스트 방법

1. **Claude Code에서 질문**
   ```
   노트북LM으로 새 노트북 만들어줘
   ```

2. **노트북 생성 확인**
   - Claude Code가 "새 노트북을 만들었어요" 메시지를 보내면 성공! 🎉
   - [NotebookLM 웹사이트](https://notebooklm.google.com)에서도 확인 가능

---

## 트러블슈팅

### 문제 1: "MCP 서버를 찾을 수 없습니다"

**원인**: `~/.mcp.json` 파일이 제대로 저장되지 않았어요.

**해결 방법**:
1. 터미널에서 `cat ~/.mcp.json` 실행
2. 설정 내용이 올바른지 확인
3. 잘못되었으면 다시 [2번](#2-mcp-서버-설정) 진행

### 문제 2: "인증이 필요합니다 (Authentication Required)"

**원인**: Google 로그인이 안 되었거나 세션이 만료되었어요.

**해결 방법**:
1. 터미널에서 `npx notebooklm-mcp-cli login` 실행
2. 브라우저에서 Google 로그인
3. 다시 스킬 실행

### 문제 3: "NotebookLM 접근 권한이 없습니다"

**원인**: 로그인한 Google 계정이 NotebookLM에 접근할 수 없어요.

**해결 방법**:
1. [NotebookLM 웹사이트](https://notebooklm.google.com) 접속
2. 같은 Google 계정으로 로그인되는지 확인
3. 안 되면 다른 Google 계정으로 재시도

### 문제 4: "npx: command not found"

**원인**: Node.js가 설치되지 않았어요.

**해결 방법**:
1. [Node.js 다운로드](https://nodejs.org/) (LTS 버전 권장)
2. 설치 후 터미널 재시작
3. `node --version` 명령어로 확인

---

## 추가 참고 자료

- [NotebookLM MCP CLI GitHub](https://github.com/jacob-bd/notebooklm-mcp-cli)
- [NotebookLM 공식 사이트](https://notebooklm.google.com)
- [MCP (Model Context Protocol) 소개](https://modelcontextprotocol.io)

---

**설정이 완료되면 워크샵에서 만나요!** 🚀

> ⚠️ **다시 한번**: 막히면 Claude Code에게 물어보세요! "노트북LM 설정이 안 돼요" 하고 물어보면, Claude Code가 최신 문서를 찾아서 도와드릴 거예요.
