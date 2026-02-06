# OpenAI Coach GPT 설정 가이드

이 가이드는 daily-focus 스킬에서 사용할 OpenAI Coach GPT를 설정하는 방법을 안내합니다.

## 개요

- **소요 시간**: 약 10분
- **필요한 것**: OpenAI 계정 (유료 API 사용)
- **비용**: GPT-4 API 사용 시 입력/출력 토큰당 과금

## 1. OpenAI API Key 발급

1. [OpenAI Platform](https://platform.openai.com) 접속 및 로그인
2. 왼쪽 메뉴에서 **API keys** 클릭
3. "Create new secret key" 클릭
4. 키 정보 입력:
   - **Name**: `Daily Focus Coach` (선택사항)
   - **Permissions**: All (기본값)
5. "Create secret key" 클릭
6. **API Key 복사** (sk-proj-로 시작)
   - ⚠️ 이 키는 한 번만 표시되므로 반드시 복사하세요!

## 2. Coach GPT Assistant 생성

### 방법 1: OpenAI Playground에서 생성 (권장)

1. [Assistants](https://platform.openai.com/assistants) 페이지 접속
2. "Create" 클릭
3. Assistant 설정:

#### Name
```
Daily Focus Coach
```

#### Instructions
```
당신은 생산성 코치입니다. 사용자가 하루 동안 집중한 한 가지 일에 대한 회고를 돕습니다.

목표:
1. 사용자의 진행 상황을 객관적으로 분석
2. 왜 목표를 달성했는지/못했는지 깊이 있는 질문
3. 다음 날을 위한 실행 가능한 조언 제공
4. 격려와 동기부여

스타일:
- 친근하지만 전문적
- 질문 중심 (Why 5번 기법 활용)
- 구체적이고 실행 가능한 조언
- 긍정적 강화와 성장 마인드셋

회고 구조:
1. **달성률 분석**: 목표 대비 실제 진행 상황
2. **근본 원인 탐색**: 성공/실패 요인 깊이 파악
3. **학습 포인트**: 이 경험에서 배울 점
4. **다음 액션**: 내일을 위한 구체적 제안
```

#### Model
```
gpt-4o (또는 최신 GPT-4 모델)
```

4. "Save" 클릭
5. **Assistant ID 복사** (asst-로 시작)

### 방법 2: Python API로 생성

```python
from openai import OpenAI

client = OpenAI(api_key="sk-proj-xxxxxxxxxxxx")

assistant = client.beta.assistants.create(
    name="Daily Focus Coach",
    instructions="""당신은 생산성 코치입니다. 사용자가 하루 동안 집중한 한 가지 일에 대한 회고를 돕습니다.

목표:
1. 사용자의 진행 상황을 객관적으로 분석
2. 왜 목표를 달성했는지/못했는지 깊이 있는 질문
3. 다음 날을 위한 실행 가능한 조언 제공
4. 격려와 동기부여

스타일: 친근하지만 전문적, 질문 중심, 구체적""",
    model="gpt-4o"
)

print(f"Assistant ID: {assistant.id}")
```

## 3. 환경변수 설정

`.env` 파일에 다음 내용 추가:

```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxx
COACH_GPT_ID=asst_xxxxxxxxxxxx
```

## 4. 테스트

```bash
python3 scripts/coach_gpt.py --reflection "오늘 PRD 초안을 75% 완료했어요. Part 2가 예상보다 어려웠어요."
```

성공하면:
```
🧑‍🏫 Coach GPT에게 피드백을 요청 중...
--------------------------------------------------
💭 회고: 오늘 PRD 초안을 75% 완료했어요. Part 2가 예상보다 어려웠어요.
--------------------------------------------------

📝 Coach 피드백:
75% 달성은 훌륭한 진전이에요! Part 2가 예상보다 어려웠다는 점을 짚어볼까요?

질문 1: Part 2에서 구체적으로 어떤 부분이 어려웠나요?
...
```

## Coach 프롬프트 커스터마이징

### 더 친근한 톤

```
당신은 친근한 동료 코치입니다. 반말로 대화하고, 이모지를 적절히 사용하세요.
```

### 더 분석적인 톤

```
당신은 데이터 기반 생산성 분석가입니다. 객관적 지표와 패턴을 중심으로 피드백하세요.
```

### 특정 분야 전문

```
당신은 제품 개발 전문 코치입니다. PRD, 디자인 스프린트, 유저 리서치 등
제품 개발 프로세스에 특화된 조언을 제공하세요.
```

## 비용 최적화 팁

1. **모델 선택**:
   - `gpt-4o`: 고품질, 높은 비용
   - `gpt-4o-mini`: 균형잡힌 품질/비용
   - `gpt-3.5-turbo`: 저렴, 기본적인 피드백

2. **프롬프트 간결화**:
   - Instructions를 핵심만 남기면 입력 토큰 절약

3. **사용량 모니터링**:
   - [OpenAI Usage](https://platform.openai.com/usage) 페이지에서 확인

## 문제 해결

### "Incorrect API key" 오류

→ `OPENAI_API_KEY`가 올바르지 않습니다. 키를 다시 확인하세요.

### "Assistant not found" 오류

→ `COACH_GPT_ID`가 올바르지 않거나 Assistant가 삭제되었습니다.

### 응답이 너무 길거나 짧음

→ Instructions에 길이 제한 추가:
```
응답은 200-300단어로 간결하게 작성하세요.
```

## 다음 단계

OpenAI 설정이 완료되었다면:
- [Slack 설정](slack-setup.md)
- [Lark 설정](lark-setup.md)
- 모든 설정이 완료되면 [SKILL.md](../SKILL.md)로 돌아가기
