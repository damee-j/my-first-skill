# daily-focus 설계서

> 📋 **이 설계서는 [사전설문응답.md](사전설문응답.md) 인터뷰를 바탕으로 작성되었습니다.**

> ⚠️ **이 설계서는 초안입니다!**
>
> 정답이 아니에요. 워크샵 당일 강사님과 함께 범위를 더 좁히거나, 더 구체화할 수 있습니다.
>
> **사전과제의 목적**:
> 1. 스킬을 설치해서 한 번 써본 것 ✅
> 2. 나만의 스킬 설계서를 만들어서 "아, 내 작업이 이렇게 자동화되겠구나", "이런 흐름이겠구나" 감 잡기 ✅
>
> 이 정도면 충분해요! 나머지는 워크샵에서 함께 다듬어봐요 😊

## 목차
- [0. 선언](#0-선언)
- [한눈에 보기](#한눈에-보기)
- [Core](#core-필수)
- [외부 API 연동](#외부-api-연동)
- [다음 단계](#다음-단계)

---

## 0. 선언

- **스킬 이름**: `daily-focus`
- **한 줄 설명**: Slack 봇이 매일 10시에 말을 걸어 오늘 집중할 딱 한 가지 일을 정하고, 필요한 시간만큼 Lark 캘린더에 Focus Block을 자동 생성하는 집중력 도우미
- **만드는 사람**: Head of Product
- **스킬 유형**: [x] 외부 API  [x] 다단계 워크플로우
- **MVP 목표**: "아침 10시에 Slack 봇이 자동으로 DM을 보내서 오늘 집중할 한 가지 일을 정하고, 스콥을 분석해서 필요한 시간만큼 Lark 캘린더 빈 시간에 Focus Block을 생성. 저녁 7시에 회고 (개인 Slack 워크스페이스 사용)"

---

## 한눈에 보기

### 외부 연동

| 서비스 | 용도 | 연동 방식 | 복잡도 | 가이드 |
|--------|------|----------|--------|--------|
| Slack | 봇 DM 발송 (대화/회고) | Bot Token | 쉬움 | Slack API |
| Lark | 캘린더 관리 (Focus Block 생성) | OAuth 2.0 | 중간 | [📘 설정 가이드](연동가이드/lark.md) |
| OpenAI | Coach GPT 회고 피드백 | API Key | 쉬움 | OpenAI Platform |

> 📁 상세 설정 가이드: [연동가이드/](연동가이드/) 폴더 참조
>
> 💡 **프라이버시**: Slack은 개인 워크스페이스를 사용하므로 회고 내용이 회사 관리자에게 노출되지 않습니다.

**예상 설정 시간**: 약 50분 (워크샵 전 사전 설정 권장)

### 워크플로 시각화

> 💡 **다이어그램이 안 보이나요?**
>
> VSCode에서 Mermaid 다이어그램을 보려면 확장 프로그램이 필요해요:
> 1. VSCode 왼쪽 사이드바에서 **확장(Extensions)** 아이콘 클릭 (또는 `Cmd+Shift+X`)
> 2. `Markdown Preview Mermaid Support` 검색
> 3. **Install** 클릭
> 4. 이 파일을 다시 열고 **미리보기**(`Cmd+Shift+V`)로 확인!

**아침 플로우 (10:00)**:
```mermaid
flowchart LR
    Start([⏰ 10:00]) --> BotPing[💬 Slack DM<br/>인사]
    BotPing --> Ask[❓ 오늘 집중할<br/>딱 한 가지]
    Ask --> Reply[💭 사용자<br/>답변]
    Reply --> Scope[📏 스콥<br/>분석]
    Scope --> CalcTime[⏱️ 필요시간<br/>계산]
    CalcTime --> FindGap[🔍 Lark 캘린더<br/>빈 시간 찾기]
    FindGap --> CreateBlock[🔒 Focus Block<br/>생성]
    CreateBlock --> Summary[📋 Slack으로<br/>요약 전송]
    Summary --> End([✅ 완료])

    style BotPing fill:#e8d5f5,stroke:#9c27b0,stroke-width:3px
    style Scope fill:#fff4e1
    style CalcTime fill:#fff4e1
    style FindGap fill:#e8d5f5,stroke:#9c27b0,stroke-width:3px
    style CreateBlock fill:#e8d5f5,stroke:#9c27b0,stroke-width:3px
    style Summary fill:#e8d5f5,stroke:#9c27b0,stroke-width:3px
    style End fill:#e8f5e9
```

**저녁 플로우 (19:00)**:
```mermaid
flowchart LR
    Start([⏰ 19:00]) --> BotPing[💬 Slack DM<br/>회고 요청]
    BotPing --> CheckCal[📅 Lark 캘린더<br/>Focus Block 확인]
    CheckCal --> Ask[❓ 오늘 한 가지<br/>어떻게 됐나요?]
    Ask --> Reply[💭 사용자<br/>답변]
    Reply --> Coach[🧑‍🏫 Coach GPT<br/>피드백]
    Coach --> SaveLog[💾 로그<br/>저장]
    SaveLog --> Share[📤 Slack으로<br/>피드백 전달]
    Share --> End([✅ 완료])

    style BotPing fill:#e8d5f5,stroke:#9c27b0,stroke-width:3px
    style CheckCal fill:#e8d5f5,stroke:#9c27b0,stroke-width:3px
    style Coach fill:#fff4e1
    style SaveLog fill:#fff4e1
    style Share fill:#e8d5f5,stroke:#9c27b0,stroke-width:3px
    style End fill:#e8f5e9
```

---

## Core (필수)

### 1. 언제 쓰나요?

**대표 상황**:
- 아침: 하루를 시작하면서 오늘 집중할 딱 한 가지를 정하고 싶을 때
- 미팅에 치여서 정작 중요한 일을 못 하는 상황을 개선하고 싶을 때
- 저녁: 하루를 마무리하면서 오늘 한 가지 일이 어떻게 됐는지 돌아보고 싶을 때

**왜 필요한가**:
- 현재: 미팅이 너무 많아서 중요한 일에 집중 못함. 캘린더에 빈 시간이 생기면 또 미팅이 끼어들어서 집중할 시간이 없음
- 목표: 매일 "딱 한 가지" 가장 중요한 일을 정의하고, 필요한 시간만큼 캘린더에 Focus Block을 만들어서 미팅이 침범하지 못하게 보호
- 빈도: 매일 (아침 10시 자동, 저녁 7시 자동)

### 2. 사용법

**이렇게 부르면**:
- 자동 트리거: 아침 10시, 저녁 7시 (설정 가능)
- 수동 트리거: `/daily-focus` (아침), `/daily-review` (저녁)
- 개인 Slack 워크스페이스 DM으로 봇이 먼저 말을 걸어옴

**결과물 형태**: [x] Slack DM (대화/회고)  [x] Lark 캘린더 Focus Block (미팅 보호)

**결과물 예시**:
> **🌅 좋은 아침이에요!**
>
> 오늘 딱 한 가지, 가장 집중하고 싶은 일은 뭐예요?
>
> [사용자 답변 후]
>
> **🎯 오늘의 Focus**
> "신규 기능 PRD 초안 작성"
>
> **📏 스콥 분석**
> - 복잡도: 중간
> - 예상 필요 시간: 3시간
>
> **🔒 Focus Block 생성 완료**
> - 14:00-15:30 (1.5시간)
> - 16:00-18:00 (2시간)
> - 총 3.5시간 확보
>
> 이 시간엔 미팅이 끼어들 수 없어요! 집중해봐요 💪

### 3. 입력/출력 명세

| 구분 | 내용 |
|------|------|
| **사용자 입력** | 자연어 (오늘 집중할 딱 한 가지 일) |
| **필수 옵션** | 없음 (대화형) |
| **선택 옵션** | 필요시간 직접 지정 (기본: AI가 스콥 분석해서 계산) |
| **출력 규칙** | Lark 메시지 + 캘린더 Focus Block (빈 시간에 자동 배치) |

### 4. 범위

**하는 것**:
1. 아침 10시: 개인 Slack DM으로 능동적으로 말 걸기 → 딱 한 가지 집중할 일 대화 → 스콥 분석 → 필요시간 계산 → Lark 캘린더 빈 시간 찾기 → Focus Block 생성 (미팅 보호) → Slack으로 요약 전송
2. 저녁 7시: Slack DM으로 회고 요청 → 오늘 한 가지 일 어떻게 됐는지 대화 → **Coach GPT 피드백** → 로그 저장 → Slack으로 피드백 전달
3. 대화 기반 입력 (자연어 이해)
4. AI 스콥 분석 (일의 복잡도와 필요시간 추정)
5. Coach GPT 연동 (회고 시 전문적인 코칭 피드백)
6. 개인 Slack 워크스페이스 사용 (프라이버시 보호)

**안 하는 것**:
1. 자동 우선순위 제안 (사용자가 직접 정의)
2. 복잡한 프로젝트 관리 (딱 한 가지에만 집중)
3. 여러 개의 작업 관리 (Top 3 아님, Only 1)

### 5. 데이터/도구/권한

| 항목 | 내용 |
|------|------|
| **읽는 데이터** | Lark 캘린더 (오늘 일정, 빈 시간 확인) |
| **쓰는 위치** | Lark 캘린더 (Focus Block 생성), Slack DM (대화/회고), 로컬 회고 로그 |
| **외부 서비스** | Slack (Bot API), Lark (Calendar API), OpenAI (Coach GPT) |
| **민감정보** | Slack Bot Token, Lark User Access Token, OpenAI API Key, 개인 일정, 회고 내용 |

### 6. 실패/예외 처리

**예상되는 실패 상황**:
1. Lark 그룹에 메시지 발송 실패
2. 캘린더에 빈 시간이 충분하지 않음 (필요시간 vs 가용시간)
3. 사용자가 응답하지 않음

**실패 시 안내 원칙**:
- Slack 메시지 실패: "Slack에 메시지를 보낼 수 없어요. 봇 권한을 확인해주세요."
- Lark 캘린더 접근 실패: "Lark 캘린더에 접근할 수 없어요. 토큰을 다시 발급받아주세요."
- 빈 시간 부족: "오늘 캘린더에 빈 시간이 [X]시간밖에 없어요. [필요시간]시간 필요한데, 일정을 조정하거나 작업 범위를 줄일까요?"
- 무응답: 1시간 후 재시도 (최대 1회)

### 7. 대화 시나리오

**정상 케이스 (아침 10시)**:

**Slack 봇 (DM, 자동)**: "🌅 좋은 아침이에요! 오늘 딱 한 가지, 가장 집중하고 싶은 일은 뭐예요?"

**나**: "신규 기능 PRD 초안 작성"

**Slack 봇**:
> 좋아요! 스콥을 분석해볼게요...
>
> **🎯 오늘의 Focus**
> "신규 기능 PRD 초안 작성"
>
> **📏 스콥 분석**
> - 작업 복잡도: 중간
> - 예상 필요 시간: 3시간
> - 분석 근거: 초안 작성은 리서치, 구조화, 초안 작성 3단계 필요
>
> **📅 오늘 일정 확인 중...**
> - 11:00-12:15 경서님 환영 점심 (1.25h)
> - 12:30-17:00 Claude Code Workshop (4.5h)
> - 가용 시간: 10:00-11:00 (1h), 17:00-19:00 (2h)
>
> **🔒 Focus Block 생성 완료!**
> - 10:00-11:00 (1시간) "PRD 초안 작성 - Part 1"
> - 17:00-19:00 (2시간) "PRD 초안 작성 - Part 2"
> - 총 3시간 확보
>
> 이 시간엔 다른 미팅이 끼어들 수 없어요! 집중해봐요 💪

**정상 케이스 (저녁 7시)**:

**Slack 봇 (DM, 자동)**: "🌙 하루 고생하셨어요! 오늘 집중했던 'PRD 초안 작성', 어떻게 됐나요?"

**나**: "Part 1은 완료했고, Part 2는 50%만 했어. 피곤해서..."

**Slack 봇**:
> 잠시만요, Coach와 함께 회고해볼게요...
>
> **🎯 오늘의 Focus**
> "신규 기능 PRD 초안 작성"
>
> **📊 결과**
> - Focus Time: 3시간 중 2.5시간 실제 활용
> - 진행률: 약 75% 완료
>
> **🧑‍🏫 Coach 피드백**
> 75% 달성은 훌륭해요! 다만 Part 2에서 속도가 느려진 이유를 살펴볼 필요가 있어요.
>
> **질문 1**: 17시 이후 집중력이 떨어진 게 단순히 피로 때문일까요, 아니면 작업의 난이도가 예상보다 높았나요?
>
> **질문 2**: Part 1과 Part 2의 차이가 무엇이었나요? 혹시 Part 2에 막히는 부분이 있었나요?
>
> **제안**: 내일은 가장 어려운 부분을 오전 Focus Block에 배치하고, 오후에는 상대적으로 가벼운 작업을 하는 건 어떨까요?
>
> **💡 다음 액션**
> 내일 "PRD 초안 완성 (나머지 25%)"을 오전 10:00-11:00에 배치할까요?
>
> 편히 쉬세요! 😊

### 8. 테스트 & 완료 기준

**테스트 체크리스트**:
- [ ] 아침 10시 자동 메시지 발송
- [ ] 딱 한 가지 일 입력 → 스콥 분석 → 필요시간 계산
- [ ] 캘린더 빈 시간 찾기 (미팅 사이사이)
- [ ] Focus Block 자동 생성 (필요시간만큼 분할 배치)
- [ ] 저녁 7시 회고 메시지 발송
- [ ] 회고 내용 → Coach GPT 전달 → 피드백 받기
- [ ] Coach GPT 피드백을 Lark로 전달
- [ ] 무응답 시 1시간 후 재시도
- [ ] 빈 시간 부족 시 경고 및 조정 제안

**Done 기준**:
"하루 동안 Slack 봇이 아침 10시/저녁 7시 2번 DM으로 말 걸어서, 오늘 집중할 한 가지 일이 정해지고 필요한 시간만큼 Lark 캘린더 빈 시간에 Focus Block이 생성되며, 저녁에 Coach GPT의 전문적인 피드백과 함께 회고가 Slack DM으로 전달되어 기록되는 것"

---

## 외부 API 연동

3개의 외부 서비스 연동이 필요합니다.

### 환경변수 요약

| 변수명 | 서비스 | 발급 방법 |
|--------|--------|----------|
| `SLACK_BOT_TOKEN` | Slack | [Slack API](https://api.slack.com/apps) → 앱 생성 → Bot Token (xoxb-로 시작) |
| `SLACK_USER_ID` | Slack | Slack 워크스페이스에서 본인 User ID 확인 |
| `LARK_APP_ID` | Lark | [Lark 개발자 콘솔](https://open.larksuite.com) → 앱 생성 → App ID 복사 |
| `LARK_APP_SECRET` | Lark | [Lark 개발자 콘솔](https://open.larksuite.com) → 앱 생성 → App Secret 복사 |
| `LARK_USER_TOKEN` | Lark | OAuth 플로우로 사용자 인증 후 자동 발급 (스킬이 자동 처리) |
| `OPENAI_API_KEY` | OpenAI | [OpenAI Platform](https://platform.openai.com/api-keys) → API Keys → Create new secret key |
| `COACH_GPT_ID` | OpenAI | Custom GPT ID 또는 Assistant ID |

> **Tip**:
> - Slack은 개인 워크스페이스를 사용하므로 회고 내용이 안전합니다! 📱
> - Lark OAuth 로그인은 스킬이 자동으로 처리해요! App ID와 Secret만 설정하면 됩니다.
> - Coach GPT ID는 ChatGPT의 Custom GPT 설정에서 확인하거나, OpenAI Assistant API로 생성한 Assistant ID를 사용하세요.

### 연동 상세

#### Slack Bot API (양방향)

| 항목 | 내용 |
|------|------|
| **Context7 Library ID** | `/slackapi/python-slack-sdk` |
| **필요한 credential** | Bot User OAuth Token |
| **환경변수** | `SLACK_BOT_TOKEN`, `SLACK_USER_ID` |
| **복잡도** | 쉬움 |
| **예상 설정 시간** | 20분 |

**설정 가이드 요약**:
1. [Slack API](https://api.slack.com/apps) 접속 → "Create New App" → "From scratch"
2. 앱 이름 입력 (예: "Daily Focus Bot") → 개인 워크스페이스 선택
3. **OAuth & Permissions** 메뉴에서 Bot Token Scopes 추가:
   - `chat:write` (메시지 발송)
   - `im:write` (DM 발송)
   - `users:read` (사용자 정보 읽기)
4. **Install to Workspace** 클릭 → **Bot User OAuth Token** 복사 (xoxb-로 시작)
5. Slack에서 본인 User ID 확인:
   - Slack 프로필 클릭 → "Copy member ID" 또는
   - API 호출: `https://slack.com/api/users.list`
6. `.env` 파일에 설정:
   ```bash
   SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx
   SLACK_USER_ID=U01XXXXXXXXX
   ```

> 💡 **프라이버시**: 개인 Slack 워크스페이스를 사용하므로 회사 관리자가 회고 내용을 볼 수 없습니다.

#### Lark Calendar API (캘린더만)

| 항목 | 내용 |
|------|------|
| **Context7 Library ID** | `/websites/open_larksuite_document` |
| **필요한 credential** | User Access Token (OAuth 2.0) |
| **환경변수** | `LARK_APP_ID`, `LARK_APP_SECRET`, `LARK_USER_TOKEN` (자동) |
| **복잡도** | 중간 |
| **예상 설정 시간** | 30분 |

**설정 가이드 요약**:
1. [Lark 개발자 콘솔](https://open.larksuite.com) 접속
2. "Create App" → 앱 이름 입력 (예: "Daily Focus Calendar")
3. 권한 추가:
   - `calendar:calendar` (캘린더 읽기/쓰기)
4. "Install to Workspace" → User Access Token 발급 (OAuth)
5. Redirect URL 등록: `http://localhost:8080/callback`
6. 스케줄 설정 (cron job): 아침 10시, 저녁 7시

**추가 설정: 스케줄러**

매일 아침 10시와 저녁 7시에 자동으로 스킬을 실행하려면 cron job을 설정하세요:

```bash
# crontab 편집
crontab -e

# 아래 내용 추가 (맥/리눅스)
0 10 * * * cd /Users/damee/dev/my-first-skill/daily-focus && /usr/local/bin/python3 morning_flow.py >> ~/daily-focus.log 2>&1
0 19 * * * cd /Users/damee/dev/my-first-skill/daily-focus && /usr/local/bin/python3 evening_flow.py >> ~/daily-focus.log 2>&1
```

> 💡 **Tip**:
> - Python 경로 확인: `which python3`
> - 로그는 `~/daily-focus.log`에 저장됩니다
> - 맥북이 꺼져있으면 실행되지 않으니 주의하세요
> - 항상 켜져있는 서버가 필요하면 GitHub Actions나 Railway 같은 클라우드 서비스를 사용하세요

> 📘 상세 가이드: [연동가이드/lark.md](연동가이드/lark.md)

#### OpenAI Coach GPT (단방향)

| 항목 | 내용 |
|------|------|
| **Context7 Library ID** | `/openai/openai-python` |
| **필요한 credential** | OpenAI API Key |
| **환경변수** | `OPENAI_API_KEY`, `COACH_GPT_ID` |
| **복잡도** | 쉬움 |
| **예상 설정 시간** | 10분 |

**설정 가이드 요약**:
1. [OpenAI Platform](https://platform.openai.com) 접속 → 로그인
2. 왼쪽 메뉴에서 "API keys" 클릭
3. "Create new secret key" 클릭 → 이름 입력 (예: "Daily Focus") → 복사
4. Coach GPT 설정:
   - **방법 1 (Custom GPT)**: ChatGPT에서 만든 Coach GPT의 ID 확인
   - **방법 2 (Assistant API)**: [Assistants](https://platform.openai.com/assistants) 페이지에서 새 Assistant 생성 → ID 복사
5. `.env` 파일에 설정:
   ```bash
   OPENAI_API_KEY=sk-proj-xxxxxxxxxxxx
   COACH_GPT_ID=asst_xxxxxxxxxxxx  # Assistant ID
   ```

**Coach GPT 프롬프트 예시**:
```
당신은 생산성 코치입니다. 사용자가 하루 동안 집중한 한 가지 일에 대한 회고를 돕습니다.

목표:
1. 사용자의 진행 상황을 객관적으로 분석
2. 왜 목표를 달성했는지/못했는지 깊이 있는 질문
3. 다음 날을 위한 실행 가능한 조언 제공
4. 격려와 동기부여

스타일: 친근하지만 전문적, 질문 중심, 구체적
```

---

## 다음 단계

### 워크샵 전 준비사항

1. **환경변수 설정** (`.env.example` 참조)
2. **Lark 봇 생성** ([연동가이드/lark.md](연동가이드/lark.md) 참조)
3. **스케줄러 설정** (cron job 또는 Lark Scheduled Message)

### 워크샵 당일

1. 이 설계서 가져오기
2. 강사님과 범위 조정 (필요시)
3. 스킬 구현 시작!

### 구현 후 (배포)

워크샵에서 스킬을 완성한 후:

1. Claude Code에게 "이 스킬 배포해줘"라고 말하기
2. GitHub 레포 자동 생성
3. 설치 명령어 받기
4. 팀원들에게 공유!

---

## 나중에 더 발전시킬 아이디어

- [ ] 주간 리포트 (월요일 아침 지난주 요약)
- [ ] 패턴 분석 (자주 미루는 태스크 알림)
- [ ] 팀원과 공유 (팀 대시보드)
- [ ] Slack 연동 (Lark 대신)

---

**워크샵 당일 이 설계서 가져오세요!** 🚀
