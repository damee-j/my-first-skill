# 채용 평가 에이전트 스킬 설계 계획

## Context

프로덕트 본부의 채용 프로세스를 자동화하는 Claude Code 스킬.
- **대상 직무**: Product Manager, Product Designer
- **3단계 프로세스**: 서류심사 → 면접질문 생성 → 항목별 평가/합불 판정
- **각 단계를 독립 에이전트로 구성**, 통합 스킬(`/recruit`)로 호출
- **참조 문서**: JD, 역량 평가기준, 면접평가표 (PDF/워드 파일로 제공)
- **결과 출력**: 콘솔 출력

## Implementation Plan

### Phase 1: 스킬 프레임워크

1. `recruitment-evaluation/SKILL.md` — 스킬 정의 (YAML frontmatter + 워크플로우)
2. `recruitment-evaluation/CLAUDE.md` — 개발자 가이드

### Phase 2: 에이전트 프롬프트

3개 에이전트 각각의 시스템 프롬프트:

| 에이전트 | 파일 | 입력 | 출력 |
|---------|------|------|------|
| 서류심사 | `agents/screen-agent.md` | JD + 역량기준 + 이력서/포트폴리오 | 합격/불합격 + 근거 |
| 면접질문 생성 | `agents/interview-agent.md` | JD + 역량기준 + 이력서 + 서류심사결과 | 45분 면접질문 구성 |
| 면접평가 | `agents/evaluate-agent.md` | 면접평가표 + 면접질문 + 면접 응답기록 | 항목별 점수 + 합불 판정 |

### Phase 3: 출력 템플릿

- `templates/screen-result.md` — 서류심사 결과 포맷
- `templates/interview-questions.md` — 면접질문지 포맷
- `templates/evaluation-report.md` — 평가 리포트 포맷

### Phase 4: 참조 문서 가이드

- `references/README.md` — 참조 문서 배치 안내

## Critical Files

```
recruitment-evaluation/
├── SKILL.md                          # 스킬 정의 (핵심)
├── CLAUDE.md                         # 개발자 가이드
├── agents/
│   ├── screen-agent.md               # 서류심사 에이전트
│   ├── interview-agent.md            # 면접질문 생성 에이전트
│   └── evaluate-agent.md             # 면접평가 에이전트
├── templates/
│   ├── screen-result.md              # 서류심사 결과 템플릿
│   ├── interview-questions.md        # 면접질문지 템플릿
│   └── evaluation-report.md          # 평가 리포트 템플릿
├── references/
│   ├── README.md                     # 참조 문서 배치 안내
│   ├── jd/                           # JD 파일 (PDF/워드)
│   ├── criteria/                     # 역량 평가기준 파일
│   └── interview-forms/              # 면접평가표 파일
└── candidates/                       # 후보자 이력서/포트폴리오 업로드
```

## Verification

- 스킬 호출 테스트: `/recruit` 명령 실행 확인
- 각 에이전트 독립 실행 가능 여부 확인
- 참조 문서 없이 실행 시 안내 메시지 출력 확인
