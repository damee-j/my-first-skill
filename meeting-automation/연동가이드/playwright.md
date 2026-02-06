# Playwright 브라우저 자동화 가이드

> 📚 **참고 문서**: Context7에서 조사한 [Playwright 공식 문서](https://playwright.dev)
>
> ⚠️ **안내**: 이 가이드는 AI가 공식 문서를 참고하여 작성했으며, 정확하지 않을 수 있습니다.
> 설정하다가 막히면 Claude Code에게 "이 부분이 안 돼요"라고 물어보면서 진행하세요!
> Claude Code가 최신 문서를 다시 찾아서 도와드릴 거예요 😊

## 목차
- [1. 사전 준비](#1-사전-준비)
- [2. Playwright 설치](#2-playwright-설치)
- [3. 브라우저 설치](#3-브라우저-설치)
- [4. 세션 저장 (로그인 유지)](#4-세션-저장-로그인-유지)
- [5. 테스트](#5-테스트)
- [트러블슈팅](#트러블슈팅)

---

## 1. 사전 준비

**필요한 것**:
- Node.js 설치 (보통 이미 설치되어 있음)
- 네이버 계정 (클로바노트 접근용)

**예상 시간**: 20-30분

**Playwright란?**: 웹 브라우저를 자동으로 조작할 수 있게 해주는 도구예요. 클로바노트에서 음성기록을 자동으로 다운로드하는 데 사용합니다.

---

## 2. Playwright 설치

### 방법 1: 스킬 폴더에서 설치 (추천)

1. **터미널 열기**
   - macOS: `Cmd + Space` → "Terminal" 입력
   - Windows: `Win + R` → "cmd" 입력

2. **스킬 폴더로 이동**
   ```bash
   cd ~/dev/my-first-skill/meeting-automation
   ```

3. **Playwright 설치**
   ```bash
   npm install playwright
   ```

4. **설치 확인**
   - 터미널에 "added [숫자] packages" 메시지가 보이면 성공!

### 방법 2: Claude Code에게 부탁하기

Claude Code와 대화창에서:

```
Playwright 설치해줘
```

Claude Code가 자동으로 설치해줍니다!

---

## 3. 브라우저 설치

Playwright는 자체 브라우저를 사용해요. 설치해야 해요.

1. **브라우저 설치**
   ```bash
   npx playwright install chromium
   ```
   (Chromium만 설치. Firefox나 WebKit은 필요 없어요)

2. **설치 확인**
   - 터미널에 "Browser downloaded successfully" 메시지가 보이면 성공!
   - 용량이 크니까 시간이 좀 걸릴 수 있어요 (약 300MB)

---

## 4. 세션 저장 (로그인 유지)

클로바노트에 매번 로그인하는 게 귀찮죠? 세션을 저장하면 한 번만 로그인하면 돼요.

### 첫 실행 시 (수동 로그인)

1. **스킬 실행**
   ```bash
   /meeting
   ```

2. **브라우저 자동 열림**
   - Playwright가 Chromium 브라우저를 열어요
   - 클로바노트 로그인 페이지가 나타나요

3. **네이버 로그인**
   - 평소처럼 네이버 아이디/비밀번호 입력
   - 로그인 완료

4. **세션 저장**
   - 스킬이 자동으로 로그인 정보를 저장해요
   - 다음부터는 자동 로그인!

### 세션 파일 위치

- macOS: `~/dev/my-first-skill/meeting-automation/.playwright/`
- Windows: `C:\Users\[사용자명]\dev\my-first-skill\meeting-automation\.playwright\`

**⚠️ 주의**: 이 폴더는 `.gitignore`에 포함되어 있어서 GitHub에 올라가지 않아요. 안전!

---

## 5. 테스트

Playwright가 제대로 작동하는지 테스트해볼게요.

### 테스트 방법 1: 간단한 스크립트

1. **테스트 파일 생성**
   ```bash
   nano test-playwright.js
   ```

2. **테스트 코드 입력**
   ```javascript
   const { chromium } = require('playwright');

   (async () => {
     const browser = await chromium.launch({ headless: false });
     const page = await browser.newPage();
     await page.goto('https://www.google.com');
     console.log('✅ Playwright 작동 확인!');
     await browser.close();
   })();
   ```

3. **실행**
   ```bash
   node test-playwright.js
   ```

4. **결과 확인**
   - 브라우저가 열리고 Google 페이지가 보이면 성공! 🎉

### 테스트 방법 2: 스킬 실행

```bash
/meeting
```

- 클로바노트 페이지가 자동으로 열리면 성공!

---

## 트러블슈팅

### 문제 1: "npx: command not found"

**원인**: Node.js가 설치되지 않았어요.

**해결 방법**:
1. [Node.js 다운로드](https://nodejs.org/) (LTS 버전 권장)
2. 설치 후 터미널 재시작
3. `node --version` 명령어로 확인

### 문제 2: "Browser is not installed"

**원인**: Chromium 브라우저가 설치되지 않았어요.

**해결 방법**:
```bash
npx playwright install chromium
```

### 문제 3: "Permission denied"

**원인**: 설치 권한이 없어요.

**해결 방법** (macOS/Linux):
```bash
sudo npm install playwright
```

**해결 방법** (Windows):
- PowerShell을 "관리자 권한"으로 실행
- 다시 설치 명령어 실행

### 문제 4: "세션이 저장되지 않아요"

**원인**: `.playwright/` 폴더가 없거나, 권한 문제예요.

**해결 방법**:
1. 폴더 생성
   ```bash
   mkdir -p .playwright
   ```

2. 권한 확인
   ```bash
   ls -la .playwright
   ```

3. 다시 스킬 실행

### 문제 5: "클로바노트 로그인이 안 돼요"

**원인**: 네이버 로그인 페이지가 변경되었거나, 보안 설정 문제예요.

**해결 방법**:
1. 수동으로 클로바노트 웹사이트 접속
2. 브라우저에서 정상 로그인 확인
3. 쿠키 및 캐시 삭제
4. 다시 스킬 실행

---

## 고급 설정 (선택사항)

### Headless 모드 (브라우저 숨기기)

브라우저 창을 보고 싶지 않다면:

```javascript
const browser = await chromium.launch({ headless: true });
```

### 브라우저 창 크기 조절

```javascript
const page = await browser.newPage({
  viewport: { width: 1920, height: 1080 }
});
```

### 타임아웃 설정

```javascript
await page.goto('https://example.com', { timeout: 60000 }); // 60초
```

---

## 추가 참고 자료

- [Playwright 공식 문서](https://playwright.dev)
- [Playwright GitHub](https://github.com/microsoft/playwright)
- [Playwright API Reference](https://playwright.dev/docs/api/class-playwright)

---

**설정이 완료되면 워크샵에서 만나요!** 🚀

> ⚠️ **다시 한번**: 막히면 Claude Code에게 물어보세요! "Playwright 설정이 안 돼요" 하고 물어보면, Claude Code가 최신 문서를 찾아서 도와드릴 거예요.
