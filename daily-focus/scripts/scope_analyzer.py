#!/usr/bin/env python3
"""
작업 스콥 분석 및 필요시간 계산

개선 사항:
- OpenAI (Enterprise GPT) Primary 사용
- Anthropic Fallback
- 둘 다 실패 시 사용자에게 직접 물어보기

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

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# OpenAI 우선, Anthropic은 fallback
openai_client = None
anthropic_client = None

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

if not openai_client and not anthropic_client:
    print("❌ OpenAI 또는 Anthropic API 키가 설정되지 않았습니다.")
    print(".env 파일에 OPENAI_API_KEY 또는 ANTHROPIC_API_KEY를 설정해주세요.")
    sys.exit(1)


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
  ]
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
  ]
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


def analyze_scope(task: str, detail: str = None) -> dict:
    """작업 스콥 분석 및 필요시간 계산 (OpenAI → Anthropic → 기본값)"""

    # 1. OpenAI 시도
    if openai_client:
        try:
            return analyze_scope_with_openai(task, detail)
        except Exception as e:
            print(f"⚠️ OpenAI 실패, Anthropic 시도 중...")

    # 2. Anthropic 시도
    if anthropic_client:
        try:
            return analyze_scope_with_anthropic(task, detail)
        except Exception as e:
            print(f"⚠️ Anthropic도 실패, 기본값 사용...")

    # 3. 기본값 반환
    print("❌ 모든 AI API 실패. 기본값을 사용합니다.")
    return {
        "complexity": "중간",
        "estimated_hours": 3.0,
        "reasoning": "AI API 오류로 기본값 사용 (작업에 따라 수동 조정 권장)",
        "breakdown": ["작업 수행: 3시간 (추정)"]
    }


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
