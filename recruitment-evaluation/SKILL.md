---
name: recruit
description: >
  프로덕트 본부 채용 평가 자동화 스킬.

  서류심사 → 면접질문 생성 → 면접평가까지 3단계 프로세스를 에이전트로 구성.

  `/recruit screen`, `/recruit interview`, `/recruit evaluate` 서브커맨드로 각 단계를 독립 실행.
---

# 채용 평가 에이전트 (Recruit)

프로덕트 본부(Product Manager, Product Designer)의 채용 프로세스를 3개 에이전트로 자동화한다. JD와 내부 평가기준을 기반으로 이력서를 심사하고, 합격자에 대해 실무 면접질문을 구성하며, 면접 후 항목별 평가와 합불 판정을 수행한다.

## Quick Start

```bash
# 1. 참조 문서 배치
#    JD 파일 → recruitment-evaluation/references/jd/
#    역량 평가기준 → recruitment-evaluation/references/criteria/
#    면접평가표 → recruitment-evaluation/references/interview-forms/

# 2. 후보자 이력서 업로드
#    이력서/포트폴리오 → recruitment-evaluation/candidates/

# 3. 스킬 실행
/recruit screen        # 서류심사
/recruit interview     # 면접질문 생성 (서류 합격자 대상)
/recruit evaluate      # 면접평가 및 합불 판정
```

## 워크플로우

### 전체 흐름

```
[JD + 평가기준] + [이력서/포트폴리오]
        │
        ▼
  ┌─────────────┐
  │  서류심사     │  → 합격/불합격 + 근거
  │  에이전트     │
  └──────┬──────┘
         │ (합격자만)
         ▼
  ┌─────────────┐
  │  면접질문     │  → 45분 면접질문지
  │  생성 에이전트 │
  └──────┬──────┘
         │ (면접 실시 후)
         ▼
  ┌─────────────┐
  │  면접평가     │  → 항목별 점수 + 합불 판정
  │  에이전트     │
  └─────────────┘
```

### Step 1: 서류심사 (`/recruit screen`)

**입력**: 직무 JD + 역량 평가기준 + 후보자 이력서/포트폴리오
**출력**: 후보자별 합격/불합격 판정 + 판정 근거

1. `references/jd/` 에서 해당 직무의 JD를 읽는다
2. `references/criteria/` 에서 해당 직무의 역량 평가기준을 읽는다
3. `candidates/` 에서 후보자의 이력서/포트폴리오를 읽는다
4. JD 필수 요건 충족 여부를 항목별로 검토한다
5. 역량 평가기준에 따라 서류 기반 역량을 평가한다
6. 합격/불합격을 판정하고 근거를 제시한다

### Step 2: 면접질문 생성 (`/recruit interview`)

**입력**: JD + 역량기준 + 후보자 이력서 + 서류심사 결과
**출력**: 45분 1차 실무 면접질문지

1. 서류심사에서 확인된 강점/약점을 기반으로 검증 포인트를 도출한다
2. 역량 평가기준의 각 항목에 대응하는 질문을 설계한다
3. 45분 시간 배분(도입 5분 / 본질문 30분 / 심화질문 5분 / 마무리 5분)에 맞춰 구성한다
4. 질문별 의도와 기대 답변 수준을 함께 제공한다

### Step 3: 면접평가 (`/recruit evaluate`)

**입력**: 면접평가표 양식 + 면접질문지 + 면접 응답 기록
**출력**: 항목별 평가 점수 + 종합 의견 + 합불 판정

1. `references/interview-forms/` 에서 면접평가표 양식을 읽는다
2. 면접 응답 기록을 각 평가 항목에 매핑한다
3. 항목별로 점수를 부여하고 근거를 작성한다
4. 종합 의견과 합격/불합격을 판정한다

## 사용법

### 서류심사 실행

```
/recruit screen

# 특정 직무 지정
/recruit screen --position PM

# 특정 후보자만 심사
/recruit screen --candidate 홍길동
```

### 면접질문 생성

```
/recruit interview

# 특정 후보자의 면접질문 생성
/recruit interview --candidate 홍길동
```

### 면접평가

```
/recruit evaluate

# 면접 응답 기록을 함께 제공
/recruit evaluate --candidate 홍길동
```

## 참조 문서 배치

| 폴더 | 내용 | 파일 형식 |
|------|------|----------|
| `references/jd/` | 직무기술서 (Job Description) | PDF, DOCX |
| `references/criteria/` | 직무별 역량 평가기준 | PDF, DOCX |
| `references/interview-forms/` | 면접평가표 양식 | PDF, DOCX |
| `candidates/` | 후보자 이력서, 포트폴리오 | PDF, DOCX |

## 범위

### 하는 것
1. JD 기반 서류 적합성 심사
2. 역량 평가기준에 따른 구조화된 평가
3. 45분 실무 면접질문지 생성 (시간 배분 포함)
4. 면접 응답 기반 항목별 평가 및 합불 판정
5. 판정 근거와 종합 의견 제공

### 안 하는 것
1. 후보자에게 직접 연락하거나 일정을 잡지 않는다
2. 이력서를 외부로 전송하지 않는다
3. 최종 합격 통보나 오퍼를 생성하지 않는다
4. 2차 이상의 면접 프로세스는 다루지 않는다

## 완료 기준

각 단계의 에이전트가 내부 평가기준에 따라 구조화된 결과물을 콘솔에 출력하면 완료.
