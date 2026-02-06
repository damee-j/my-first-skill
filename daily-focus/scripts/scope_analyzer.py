#!/usr/bin/env python3
"""
작업 스콥 분석 및 필요시간 계산

개선 사항:
- Gemini (Google Generative AI) Primary 사용 - 소요 시간 예측 + 작업 방법 조언
- OpenAI (Enterprise GPT) Fallback
- Anthropic Fallback
- 모두 실패 시 키워드 기반 휴리스틱

사용법:
    python3 scope_analyzer.py "PRD 초안 작성"
    python3 scope_analyzer.py --task "PRD 초안 작성" --detail "리서치, 구조화, 초안"
"""

import os
import sys
import json
import argparse
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Gemini 우선, OpenAI와 Anthropic은 fallback
gemini_client = None
openai_client = None
anthropic_client = None

if GEMINI_API_KEY:
    try:
        from google import genai
        from google.genai import types
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except ImportError:
        print("⚠️ google-genai 패키지가 없습니다. pip install google-genai를 실행하세요.")

if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        print("⚠️ openai 패키지가 없습니다. pip install openai를 실행하세요.")

if ANTHROPIC_API_KEY:
    try:
        import anthropic
        anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    except ImportError:
        print("⚠️ anthropic 패키지가 없습니다.")

if not gemini_client and not openai_client and not anthropic_client:
    print("❌ Gemini, OpenAI 또는 Anthropic API 키가 설정되지 않았습니다.")
    print(".env 파일에 GEMINI_API_KEY, OPENAI_API_KEY 또는 ANTHROPIC_API_KEY를 설정해주세요.")
    sys.exit(1)


def analyze_scope_with_gemini(task: str, detail: str = None) -> dict:
    """Gemini로 스콥 분석 및 작업 조언"""
    # 프롬프트 구성
    prompt = f"""작업: {task}
"""
    if detail:
        prompt += f"상세 정보: {detail}\n"

    prompt += """
당신은 생산성 전문가입니다. 주어진 작업의 스콥을 분석하고, 필요한 시간을 정확하게 추정하며, 효과적인 작업 방법을 조언하세요.

다음 형식으로 JSON 응답을 생성하세요:

{
  "complexity": "낮음|중간|높음",
  "estimated_hours": 숫자 (소수점 가능, 예: 2.5),
  "reasoning": "추정 근거 설명",
  "breakdown": [
    "단계 1: 설명 (예상 시간)",
    "단계 2: 설명 (예상 시간)"
  ],
  "advice": "작업을 효율적으로 완료하기 위한 구체적인 조언 (시작 방법, 주의사항, 집중 포인트 등)"
}

작업의 복잡도와 일반적인 수행 시간을 고려하여 현실적으로 추정하세요.
조언은 실행 가능하고 구체적이어야 합니다.
"""

    try:
        from google.genai import types

        # JSON 스키마 정의
        response_schema = {
            "type": "object",
            "properties": {
                "complexity": {"type": "string"},
                "estimated_hours": {"type": "number"},
                "reasoning": {"type": "string"},
                "breakdown": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "advice": {"type": "string"}
            },
            "required": ["complexity", "estimated_hours", "reasoning", "breakdown", "advice"]
        }

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema
        )

        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=config
        )

        result = json.loads(response.text)
        print("✅ Gemini로 스콥 분석 완료")
        return result

    except Exception as e:
        print(f"⚠️ Gemini 스콥 분석 실패: {str(e)}")
        raise


def analyze_scope_with_openai(task: str, detail: str = None) -> dict:
    """OpenAI (GPT-4)로 스콥 분석"""
    # 프롬프트 구성
    system_prompt = "당신은 생산성 전문가입니다. 주어진 작업의 스콥을 분석하고 필요한 시간을 정확하게 추정하세요."

    user_prompt = f"""작업: {task}
"""
    if detail:
        user_prompt += f"상세 정보: {detail}\n"

    user_prompt += """
다음 형식으로 JSON 응답을 생성하세요:

{
  "complexity": "낮음|중간|높음",
  "estimated_hours": 숫자 (소수점 가능, 예: 2.5),
  "reasoning": "추정 근거 설명",
  "breakdown": [
    "단계 1: 설명 (예상 시간)",
    "단계 2: 설명 (예상 시간)"
  ],
  "advice": "작업을 효율적으로 완료하기 위한 구체적인 조언"
}

작업의 복잡도와 일반적인 수행 시간을 고려하여 현실적으로 추정하세요.
"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Enterprise GPT
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1024
        )

        response_text = response.choices[0].message.content

        # JSON 추출
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        else:
            json_text = response_text.strip()

        result = json.loads(json_text)
        print("✅ OpenAI로 스콥 분석 완료")
        return result

    except Exception as e:
        print(f"⚠️ OpenAI 스콥 분석 실패: {str(e)}")
        raise


def analyze_scope_with_anthropic(task: str, detail: str = None) -> dict:
    """Anthropic (Claude)로 스콥 분석"""
    # 프롬프트 구성
    prompt = f"""당신은 생산성 전문가입니다. 주어진 작업의 스콥을 분석하고 필요한 시간을 추정하세요.

작업: {task}
"""

    if detail:
        prompt += f"\n상세 정보: {detail}\n"

    prompt += """
다음 형식으로 JSON 응답을 생성하세요:

{
  "complexity": "낮음|중간|높음",
  "estimated_hours": 숫자 (소수점 가능, 예: 2.5),
  "reasoning": "추정 근거 설명",
  "breakdown": [
    "단계 1: 설명 (예상 시간)",
    "단계 2: 설명 (예상 시간)"
  ],
  "advice": "작업을 효율적으로 완료하기 위한 구체적인 조언"
}

작업의 복잡도와 일반적인 수행 시간을 고려하여 현실적으로 추정하세요.
"""

    try:
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text

        # JSON 추출
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        else:
            json_text = response_text.strip()

        result = json.loads(json_text)
        print("✅ Anthropic으로 스콥 분석 완료")
        return result

    except Exception as e:
        print(f"⚠️ Anthropic 스콥 분석 실패: {str(e)}")
        raise


def estimate_with_heuristics(task: str) -> dict:
    """키워드 기반 휴리스틱 추정"""
    task_lower = task.lower()

    # 키워드 기반 시간 추정
    if any(word in task_lower for word in ['초안', '드래프트', 'draft', '간단', '정리']):
        hours = 2.0
        complexity = "중간"
        advice = "먼저 큰 그림을 잡고, 세부사항은 나중에 채워가세요. 완벽함보다는 빠른 피드백이 중요합니다."
    elif any(word in task_lower for word in ['prd', '기획서', '제안서', '설계', 'design', 'proposal']):
        hours = 4.0
        complexity = "높음"
        advice = "문제 정의부터 시작하세요. 리서치 → 구조화 → 작성 순서로 진행하며, 중간중간 이해관계자 피드백을 받으세요."
    elif any(word in task_lower for word in ['리뷰', 'review', '검토', '피드백', 'feedback']):
        hours = 1.5
        complexity = "낮음"
        advice = "체크리스트를 만들어 체계적으로 검토하세요. 긍정적인 부분과 개선점을 균형있게 전달하세요."
    elif any(word in task_lower for word in ['분석', 'analysis', '리서치', 'research']):
        hours = 3.0
        complexity = "중간"
        advice = "질문을 명확히 정의하고, 관련 데이터를 먼저 수집하세요. 인사이트를 시각화하면 이해가 빨라집니다."
    elif any(word in task_lower for word in ['미팅', 'meeting', '회의', '논의']):
        hours = 1.0
        complexity = "낮음"
        advice = "아젠다를 미리 공유하고, 회의 목표를 명확히 하세요. 시간 제한을 두고 진행하세요."
    elif any(word in task_lower for word in ['구현', 'implement', '개발', 'develop', '코딩', 'coding']):
        hours = 5.0
        complexity = "높음"
        advice = "작은 단위로 나눠서 진행하고, 자주 테스트하세요. 막히면 다른 사람에게 빨리 물어보는 것이 효율적입니다."
    else:
        # 기본값
        hours = 3.0
        complexity = "중간"
        advice = "작업을 작은 단위로 나누고, 우선순위가 높은 것부터 시작하세요. 중간 점검을 통해 방향을 조정하세요."

    return {
        "complexity": complexity,
        "estimated_hours": hours,
        "reasoning": f"키워드 기반 추정 (작업: '{task}')",
        "breakdown": [f"{task}: {hours}시간 (추정)"],
        "advice": advice
    }


def analyze_scope(task: str, detail: str = None, interactive: bool = False) -> dict:
    """작업 스콥 분석 및 필요시간 계산 (Gemini → OpenAI → Anthropic → 휴리스틱)"""

    # 1. Gemini 시도 (우선)
    if gemini_client:
        try:
            return analyze_scope_with_gemini(task, detail)
        except Exception as e:
            print(f"⚠️ Gemini 실패: {str(e)[:100]}...")

    # 2. OpenAI 시도
    if openai_client:
        try:
            return analyze_scope_with_openai(task, detail)
        except Exception as e:
            print(f"⚠️ OpenAI 실패: {str(e)[:100]}...")

    # 3. Anthropic 시도
    if anthropic_client:
        try:
            return analyze_scope_with_anthropic(task, detail)
        except Exception as e:
            print(f"⚠️ Anthropic 실패: {str(e)[:100]}...")

    # 3. 휴리스틱 추정 (AI 실패 시)
    print("🔍 키워드 기반 스콥 추정 중...")
    heuristic_result = estimate_with_heuristics(task)

    # 대화형 모드면 사용자에게 확인 요청
    if interactive:
        print(f"\n💡 추정 결과: {heuristic_result['estimated_hours']}시간")
        print(f"   근거: {heuristic_result['reasoning']}")
        print("\n이 추정이 적절한가요? (y/n 또는 시간을 숫자로 입력)")

        user_input = input("> ").strip()

        if user_input.lower() == 'n':
            # 사용자가 직접 입력
            print("\n몇 시간이 필요할까요? (예: 2.5)")
            hours_input = input("> ").strip()
            try:
                hours = float(hours_input)
                heuristic_result['estimated_hours'] = hours
                heuristic_result['reasoning'] = "사용자 입력"
            except:
                print("⚠️ 잘못된 입력입니다. 추정값을 사용합니다.")
        elif user_input.replace('.', '').isdigit():
            # 숫자를 직접 입력한 경우
            hours = float(user_input)
            heuristic_result['estimated_hours'] = hours
            heuristic_result['reasoning'] = "사용자 입력"

    return heuristic_result


def format_output(result: dict):
    """결과 포맷팅"""
    print("\n📏 스콥 분석 결과")
    print("=" * 50)
    print(f"복잡도: {result['complexity']}")
    print(f"예상 필요 시간: {result['estimated_hours']}시간")
    print(f"\n분석 근거:")
    print(f"  {result['reasoning']}")
    print(f"\n작업 단계:")
    for i, step in enumerate(result['breakdown'], 1):
        print(f"  {i}. {step}")
    print("=" * 50)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="작업 스콥 분석")
    parser.add_argument("task", nargs="?", type=str, help="분석할 작업")
    parser.add_argument("--detail", type=str, help="작업 상세 정보")
    parser.add_argument("--json", action="store_true", help="JSON 형식으로 출력")

    args = parser.parse_args()

    if not args.task:
        print("사용법:")
        print("  python3 scope_analyzer.py \"PRD 초안 작성\"")
        print("  python3 scope_analyzer.py --task \"PRD 초안 작성\" --detail \"리서치, 구조화, 초안\"")
        sys.exit(1)

    result = analyze_scope(args.task, args.detail)

    if args.json:
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        format_output(result)

    return result


if __name__ == "__main__":
    main()
