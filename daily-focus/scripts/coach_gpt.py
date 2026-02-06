#!/usr/bin/env python3
"""
Coach GPT 피드백 스크립트

사용법:
    python3 coach_gpt.py --reflection "오늘 PRD 75% 완료했어요"
    python3 coach_gpt.py --focus "PRD 초안 작성" --result "75% 완료" --reason "피곤해서..."
"""

import os
import sys
import argparse
from openai import OpenAI
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COACH_GPT_ID = os.getenv("COACH_GPT_ID")

if not OPENAI_API_KEY or not COACH_GPT_ID:
    print("❌ 환경변수가 설정되지 않았습니다.")
    print("OPENAI_API_KEY와 COACH_GPT_ID를 .env 파일에 설정해주세요.")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)


def get_coach_feedback(reflection: str) -> str:
    """Coach GPT로부터 피드백 받기"""
    try:
        # Thread 생성
        thread = client.beta.threads.create()

        # 메시지 추가
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=reflection
        )

        # Run 실행
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=COACH_GPT_ID
        )

        # 완료 대기
        while run.status in ["queued", "in_progress"]:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )

        if run.status == "completed":
            # 응답 조회
            messages = client.beta.threads.messages.list(
                thread_id=thread.id
            )

            # 최신 메시지 (Coach의 응답)
            for message in messages.data:
                if message.role == "assistant":
                    content = message.content[0].text.value
                    return content

            return "❌ Coach 응답을 찾을 수 없습니다."

        else:
            return f"❌ Coach 실행 실패: {run.status}"

    except Exception as e:
        return f"❌ OpenAI API 오류: {str(e)}"


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
