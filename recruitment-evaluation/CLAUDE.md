# CLAUDE.md — 채용 평가 에이전트

## Project Overview

프로덕트 본부(PM, Product Designer) 채용 프로세스를 3개 에이전트로 자동화하는 Claude Code 스킬. `/recruit` 스킬로 통합 호출하며, 서류심사·면접질문 생성·면접평가 각 단계를 독립 에이전트로 실행한다.

## Architecture

```
/recruit {subcommand}
    │
    ├─ screen    → agents/screen-agent.md 프롬프트 로드 → Agent 실행
    ├─ interview → agents/interview-agent.md 프롬프트 로드 → Agent 실행
    └─ evaluate  → agents/evaluate-agent.md 프롬프트 로드 → Agent 실행
```

**에이전트 실행 방식**: SKILL.md가 서브커맨드를 파싱하고, 해당 에이전트의 프롬프트(`agents/*.md`)를 로드하여 Agent 도구로 실행한다. 각 에이전트는 `references/` 의 참조 문서와 `candidates/` 의 후보자 자료를 읽어 평가를 수행한다.

**데이터 흐름**:
1. 참조 문서 (JD, 평가기준, 평가표) → `references/` 에 사전 배치
2. 후보자 자료 (이력서, 포트폴리오) → `candidates/` 에 업로드
3. 각 에이전트가 필요한 파일을 Read 도구로 로드
4. 결과는 콘솔에 직접 출력

## Key Commands

```bash
# 스킬 실행
/recruit screen              # 서류심사
/recruit interview           # 면접질문 생성
/recruit evaluate            # 면접평가

# 참조 문서 확인
ls recruitment-evaluation/references/jd/
ls recruitment-evaluation/references/criteria/
ls recruitment-evaluation/references/interview-forms/

# 후보자 자료 확인
ls recruitment-evaluation/candidates/
```

## File Structure

| 파일/폴더 | 용도 |
|----------|------|
| `SKILL.md` | 스킬 정의 및 사용자 가이드 |
| `agents/screen-agent.md` | 서류심사 에이전트 프롬프트 |
| `agents/interview-agent.md` | 면접질문 생성 에이전트 프롬프트 |
| `agents/evaluate-agent.md` | 면접평가 에이전트 프롬프트 |
| `references/jd/` | 직무기술서 (PDF/DOCX) |
| `references/criteria/` | 역량 평가기준 (PDF/DOCX) |
| `references/interview-forms/` | 면접평가표 양식 (PDF/DOCX) |
| `candidates/` | 후보자 이력서/포트폴리오 (PDF/DOCX) |

## 에이전트별 입출력

| 에이전트 | 입력 | 출력 |
|---------|------|------|
| screen | JD + 역량기준 + 이력서 | 합격/불합격 + 항목별 근거 |
| interview | JD + 역량기준 + 이력서 + 심사결과 | 45분 면접질문지 (질문별 의도·기대답변) |
| evaluate | 평가표 + 질문지 + 면접응답 | 항목별 점수 + 종합소견 + 합불 |

## Language

이 프로젝트의 문서와 코드 주석은 한국어로 작성한다. 사용자와의 대화도 한국어로 진행한다.
