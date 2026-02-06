#!/usr/bin/env python3
"""
Coach GPT 피드백 스크립트 (Google Gemini 사용 - 무료!)

사용법:
    python3 coach_gpt.py --reflection "오늘 PRD 75% 완료했어요"
    python3 coach_gpt.py --focus "PRD 초안 작성" --result "75% 완료" --reason "피곤해서..."
"""

import os
import sys
import argparse
import requests
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ 환경변수가 설정되지 않았습니다.")
    print("GEMINI_API_KEY를 .env 파일에 설정해주세요.")
    sys.exit(1)

# Coach 시스템 프롬프트
COACH_SYSTEM_PROMPT = """당신은 전문적이면서도 친근한 생산성 코치입니다.

당신의 역할:
- 사용자의 하루 업무 회고를 듣고 객관적으로 분석
- 목표 달성/미달성의 근본 원인을 깊이 있게 탐구
- 실행 가능한 구체적 조언 제공
- 격려와 동기부여

응답 스타일:
- 친근하지만 프로페셔널하게
- 구체적이고 실행 가능한 조언
- 2-3단락, 300-500자 정도
- 존댓말 사용
- 이모지는 최소한으로만 사용"""


def get_coach_feedback(reflection: str) -> str:
    """Coach 피드백 받기 (Google Gemini 2.5 Flash Lite - 무료!)"""
    try:
        # Gemini REST API 직접 호출 (가장 안정적)
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"

        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{COACH_SYSTEM_PROMPT}\n\n사용자 회고:\n{reflection}"
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 800,
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        if response.status_code == 200:
            feedback = data['candidates'][0]['content']['parts'][0]['text']
            return feedback
        else:
            error = data.get('error', {})
            return f"❌ Gemini API 오류: {error.get('message', str(data))}"

    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "rate_limit" in error_msg.lower():
            return "❌ Gemini API 할당량이 초과되었습니다. (무료 한도: 분당 15회)"
        return f"❌ Gemini API 오류: {error_msg}"


def format_reflection(focus: str = None, result: str = None, reason: str = None) -> str:
    """회고 내용 포맷팅"""
    parts = []

    if focus:
        parts.append(f"**오늘의 Focus**: {focus}")

    if result:
        parts.append(f"**결과**: {result}")

    if reason:
        parts.append(f"**상황**: {reason}")

    return "\n\n".join(parts)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="Coach GPT 피드백")
    parser.add_argument("--reflection", type=str, help="회고 내용 (자유 형식)")
    parser.add_argument("--focus", type=str, help="오늘 집중한 일")
    parser.add_argument("--result", type=str, help="진행 결과")
    parser.add_argument("--reason", type=str, help="이유/상황")

    args = parser.parse_args()

    if args.reflection:
        reflection = args.reflection
    elif args.focus or args.result or args.reason:
        reflection = format_reflection(args.focus, args.result, args.reason)
    else:
        print("사용법:")
        print("  python3 coach_gpt.py --reflection \"오늘 PRD 75% 완료했어요\"")
        print("  python3 coach_gpt.py --focus \"PRD 작성\" --result \"75%\" --reason \"피곤해서...\"")
        sys.exit(1)

    print("🧑‍🏫 Coach GPT에게 피드백을 요청 중...")
    print("-" * 50)
    print(f"💭 회고: {reflection}")
    print("-" * 50)

    feedback = get_coach_feedback(reflection)

    print("\n📝 Coach 피드백:")
    print(feedback)


if __name__ == "__main__":
    main()
