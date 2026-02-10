# Daily-Focus GitHub Actions 설정 가이드

GitHub Actions로 daily-focus를 24/7 자동 실행하는 방법입니다.

## 📋 개요

- **실행 시간**: 매일 10:00 KST (아침), 19:00 KST (저녁)
- **비용**: 완전 무료 (GitHub Actions 무료 티어)
- **장점**: MacBook이 꺼져있어도 작동

---

## 🚀 설정 단계

### 1. GitHub Repository에 코드 푸시

```bash
cd /Users/damee/dev/my-first-skill
git add .github/workflows/daily-focus.yml
git add daily-focus/
git commit -m "Add GitHub Actions workflow for daily-focus"
git push origin main
```

### 2. GitHub Secrets 설정

1. GitHub 저장소 페이지로 이동
2. **Settings** → **Secrets and variables** → **Actions** 클릭
3. **New repository secret** 클릭하여 아래 secrets 추가:

| Secret 이름 | 값 (from `.env`) | 설명 |
|-------------|------------------|------|
| `SLACK_BOT_TOKEN` | `xoxb-10468191240081-...` | Slack 봇 토큰 |
| `SLACK_USER_ID` | `U0AE7GEAN72` | Slack 사용자 ID |
| `SLACK_CHANNEL_NAME` | `daily-focus` | Slack 채널 이름 |
| `SLACK_CHANNEL_ID` | `C0AD6RX1R3M` | Slack 채널 ID |
| `LARK_APP_ID` | `cli_a90ee729a4389eed` | Lark 앱 ID |
| `LARK_APP_SECRET` | `uW053LW5nhMOBloQo...` | Lark 앱 Secret |
| `LARK_USER_TOKEN` | `eyJhbGciOiJFUzI1...` | Lark User 토큰 |
| `GEMINI_API_KEY` | `AIzaSyBlX2kD-lB9...` | Gemini AI API 키 |
| `OPENAI_API_KEY` | `sk-proj-BZQGNzd...` | OpenAI API 키 |
| `ANTHROPIC_API_KEY` | `sk-ant-api03-FKSn...` | Anthropic API 키 |
| `COACH_GPT_ID` | `asst_BAcPp7wK5VHm...` | Coach GPT Assistant ID |

#### Secrets 복사 방법

로컬 `.env` 파일에서 값을 복사:

```bash
cat /Users/damee/dev/my-first-skill/daily-focus/.env
```

각 줄의 `=` 오른쪽 값을 복사하여 GitHub Secret으로 추가.

---

### 3. Workflow 활성화 확인

1. GitHub 저장소 → **Actions** 탭 클릭
2. "Daily Focus Automation" 워크플로우 확인
3. 활성화되어 있는지 확인 (비활성화 상태면 **Enable workflow** 클릭)

---

### 4. 수동 테스트 실행

첫 스케줄 실행을 기다리지 말고 수동으로 테스트:

1. **Actions** 탭 → **Daily Focus Automation** 클릭
2. **Run workflow** 드롭다운 클릭
3. `Flow to run` 선택: **morning** 또는 **evening**
4. **Run workflow** 버튼 클릭

실행 결과:
- Slack DM 수신 확인
- Logs 확인: 워크플로우 실행 상세 로그 보기

---

## ⚠️ Lark User Token 만료 문제

### 문제점

- **Lark User Access Token은 약 2시간마다 만료됨**
- GitHub Actions는 브라우저가 없어 OAuth 재인증 불가능

### 해결 방법

#### 방법 1: 수동 토큰 갱신 (권장)

**주기**: 매 2시간마다 또는 토큰 만료 시

**절차**:
1. 로컬에서 토큰 재발급:
   ```bash
   cd /Users/damee/dev/my-first-skill/daily-focus
   python3 scripts/lark_oauth.py
   ```

2. 새 토큰 확인:
   ```bash
   grep LARK_USER_TOKEN .env | cut -d'=' -f2
   ```

3. GitHub Secrets 업데이트:
   - GitHub 저장소 → **Settings** → **Secrets and variables** → **Actions**
   - `LARK_USER_TOKEN` 클릭 → **Update secret**
   - 새 토큰 붙여넣기 → **Update secret**

#### 방법 2: 자동 알림 (daily-focus 내장)

`morning_flow.py`는 Lark 토큰 만료 시 자동으로 Slack DM 전송:

```
❌ Lark 캘린더 토큰이 만료되었습니다.

아래 단계로 재인증하세요:
1. 로컬에서 실행: python3 scripts/lark_oauth.py
2. GitHub Secrets의 LARK_USER_TOKEN 업데이트

재인증까지 Focus Block 생성이 중단됩니다.
```

이 메시지를 받으면 위의 **방법 1** 절차 진행.

#### 방법 3: 토큰 만료 무시 (임시)

Focus Block 없이 Slack 메시지만 받기:
- Lark 토큰 만료 시에도 morning/evening flow는 계속 실행됨
- Slack 대화는 정상 작동
- 단, Lark 캘린더 조회 및 Focus Block 생성은 스킵됨

---

## 📅 스케줄 시간

| 플로우 | KST | UTC | Cron 표현식 |
|--------|-----|-----|-------------|
| Morning | 10:00 | 01:00 | `0 1 * * *` |
| Evening | 19:00 | 10:00 | `0 10 * * *` |

**참고**: GitHub Actions는 UTC 기준이므로 KST에서 -9시간 적용.

---

## 🔍 로그 확인

### 워크플로우 실행 로그

1. GitHub → **Actions** → 실행 기록 클릭
2. `morning-flow` 또는 `evening-flow` job 클릭
3. 각 step의 로그 확인

### JSON 로그 다운로드

1. 워크플로우 실행 상세 페이지
2. **Artifacts** 섹션에서 `morning-logs-*` 또는 `evening-logs-*` 다운로드
3. `.daily-focus/*.json` 파일 확인

---

## 🛠️ 트러블슈팅

### 1. Workflow가 실행되지 않음

**원인**: GitHub Actions가 비활성화되어 있음

**해결**:
- **Actions** 탭 → Workflow 선택 → **Enable workflow**

### 2. Slack 메시지가 오지 않음

**확인 사항**:
1. GitHub Secrets의 `SLACK_BOT_TOKEN` 확인
2. 워크플로우 로그에서 에러 메시지 확인
3. Slack 앱의 Bot Token Scopes 확인:
   - `chat:write`
   - `im:write`
   - `users:read`

**테스트**:
로컬에서 Slack 연결 테스트:
```bash
cd /Users/damee/dev/my-first-skill/daily-focus
python3 scripts/slack_dm.py "GitHub Actions 테스트"
```

### 3. Lark 캘린더 조회 실패

**원인**: `LARK_USER_TOKEN` 만료

**해결**: 위의 **방법 1: 수동 토큰 갱신** 참조

### 4. Gemini/OpenAI API 에러

**확인 사항**:
1. GitHub Secrets의 API 키 확인
2. API 키 할당량 확인 (무료 티어 제한)

**로그 확인**:
```
⚠️ Gemini API 에러, OpenAI로 fallback 시도 중...
```

---

## 🚫 로컬 Cron 비활성화 (선택)

GitHub Actions가 정상 작동하면 로컬 cron은 비활성화 가능:

```bash
crontab -e
```

아래 줄 앞에 `#` 추가하여 주석 처리:
```bash
# 0 10 * * * cd /Users/damee/dev/my-first-skill/daily-focus && /usr/bin/python3 morning_flow.py >> ~/daily-focus.log 2>&1
# 0 19 * * * cd /Users/damee/dev/my-first-skill/daily-focus && /usr/bin/python3 evening_flow.py >> ~/daily-focus.log 2>&1
```

저장 후 종료 (`:wq`).

---

## 📊 비용

- **GitHub Actions 무료 티어**: 월 2,000분
- **daily-focus 사용량**: 하루 약 2-5분 (morning + evening)
- **월 예상 사용량**: 60-150분
- **결론**: 완전 무료로 충분 ✅

---

## 🎯 Next Steps

1. ✅ GitHub Secrets 설정 완료
2. ✅ 수동 테스트 실행
3. ⏳ 내일 아침 10시 자동 실행 대기
4. 📋 Lark 토큰 갱신 주기 파악 (첫 만료 시각 확인)
5. 🔄 토큰 갱신 루틴 확립

---

## 📞 문제 발생 시

1. GitHub Actions 로그 확인
2. Slack DM에서 에러 메시지 확인
3. 로컬에서 동일 플로우 실행 테스트:
   ```bash
   cd /Users/damee/dev/my-first-skill/daily-focus
   python3 morning_flow.py  # 또는 evening_flow.py
   ```

모든 설정이 완료되면 **완전 자동화된 Daily Focus 시스템** 완성! 🎉
