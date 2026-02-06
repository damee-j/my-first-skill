#!/usr/bin/env python3
"""
저녁 워크플로우 (19:00 실행)

흐름:
1. Lark 토큰 유효성 체크 (필요시 알림)
2. 아침에 저장한 로그 불러오기
3. Slack DM으로 회고 요청
4. 사용자 응답 대기 (5분 타임아웃)
5. Coach GPT 피드백 요청
6. Slack으로 피드백 전달
7. 회고 로그 업데이트
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

# 스크립트 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from slack_dm import send_dm, get_recent_messages
from coach_gpt import get_coach_feedback

# .env 파일 로드
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")


def wait_for_user_response(timeout_minutes=5):
    """사용자 응답 대기"""
    print(f"⏳ 사용자 응답 대기 중... (최대 {timeout_minutes}분)")

    start_time = time.time()
    timeout_seconds = timeout_minutes * 60

    # 현재 시간의 메시지 개수 확인
    initial_messages = get_recent_messages(limit=5)
    initial_count = len(initial_messages)

    while True:
        # 타임아웃 체크
        if time.time() - start_time > timeout_seconds:
            print("⏰ 타임아웃: 응답이 없습니다.")
            return None

        # 30초마다 새 메시지 확인
        time.sleep(30)

        current_messages = get_recent_messages(limit=5)
        if len(current_messages) > initial_count:
            # 새 메시지가 있으면 가장 최근 메시지 반환
            new_message = current_messages[0]
            if new_message["user"] != "bot":  # 봇 메시지가 아니면
                print(f"✅ 응답 받음: {new_message['text'][:50]}...")
                return new_message["text"]

        print(".", end="", flush=True)


def load_today_log():
    """오늘 아침 로그 불러오기"""
    log_dir = Path.home() / ".daily-focus"
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"{today}.json"

    if not log_file.exists():
        print("❌ 오늘 아침 로그를 찾을 수 없습니다.")
        return None

    with open(log_file, "r", encoding="utf-8") as f:
        return json.load(f)


def format_reflection_prompt(log_data, user_response):
    """회고 프롬프트 포맷팅"""
    focus_task = log_data.get("focus_task", "알 수 없음")
    scope_analysis = log_data.get("scope_analysis", {})
    estimated_hours = scope_analysis.get("estimated_hours", 0)
    focus_blocks = log_data.get("focus_blocks", [])

    total_allocated_minutes = sum(block["duration"] for block in focus_blocks)
    total_allocated_hours = total_allocated_minutes / 60

    reflection = f"""**오늘의 Focus**
"{focus_task}"

**계획**
- 예상 필요 시간: {estimated_hours}시간
- 확보한 Focus Time: {total_allocated_hours:.1f}시간

**회고**
{user_response}

---

위 내용을 바탕으로:
1. 진행 상황을 객관적으로 분석해주세요
2. 목표를 달성했거나/못했다면 그 이유를 깊이 있게 질문해주세요
3. 다음 날을 위한 실행 가능한 조언을 제공해주세요
4. 격려와 동기부여를 해주세요

친근하지만 전문적인 코치 스타일로 답변해주세요."""

    return reflection


def format_feedback_message(log_data, user_response, coach_feedback):
    """피드백 메시지 포맷팅"""
    focus_task = log_data.get("focus_task", "알 수 없음")
    focus_blocks = log_data.get("focus_blocks", [])
    total_allocated_minutes = sum(block["duration"] for block in focus_blocks)

    message = f"""🌙 **오늘의 회고**

**집중한 일**: {focus_task}
**Focus Time**: {total_allocated_minutes/60:.1f}시간
**결과**: {user_response}

---

🧑‍🏫 **Coach 피드백**

{coach_feedback}

---

💾 오늘 하루도 고생 많으셨어요! 편히 쉬세요 😊"""

    return message


def check_lark_token():
    """Lark 토큰 유효성 체크 (저녁용 - 덜 엄격)"""
    try:
        from lark_token_manager import get_valid_token, load_tokens

        token = get_valid_token()

        if not token:
            # 토큰이 만료되어도 회고는 계속 진행
            send_dm("""⚠️ **Lark 캘린더 연동 만료**

내일 아침 Focus Block을 생성하려면 Lark 재로그인이 필요해요.

시간 날 때 다음 명령어를 실행해주세요:
```
python3 ~/dev/my-first-skill/daily-focus/scripts/lark_oauth.py
```""")
            # 회고는 계속 진행
            return True

        # 토큰 만료 임박 확인
        token_data = load_tokens()
        if token_data:
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            time_left = expires_at - datetime.now()

            if time_left < timedelta(hours=12):
                send_dm(f"""⏰ **Lark 토큰 만료 주의**

토큰이 {time_left.total_seconds()/3600:.1f}시간 후에 만료됩니다.
내일 아침 전에 재로그인해주세요!""")

        return True

    except Exception as e:
        print(f"⚠️ 토큰 체크 중 오류: {e}")
        return True


def main():
    """메인 함수"""
    print("=" * 60)
    print("🌙 저녁 워크플로우 시작")
    print("=" * 60)

    # 0. Lark 토큰 체크 (선택적)
    print("\n🔐 Lark 토큰 체크 중...")
    check_lark_token()  # 결과와 관계없이 계속 진행

    # 1. 아침 로그 불러오기
    print("\n📂 오늘 아침 로그 불러오기...")
    log_data = load_today_log()

    if not log_data:
        # 로그 없으면 일반 회고
        send_dm("🌙 하루 고생하셨어요! 오늘 하루는 어땠나요?")
        user_response = wait_for_user_response(timeout_minutes=5)

        if not user_response:
            send_dm("응답이 없어서 회고를 진행하지 못했어요. 내일 만나요!")
            return

        # 로그 없이 간단한 피드백만
        reflection = f"오늘 하루: {user_response}"
        coach_feedback = get_coach_feedback(reflection)
        send_dm(f"🧑‍🏫 Coach 피드백:\n\n{coach_feedback}\n\n편히 쉬세요! 😊")
        return

    focus_task = log_data.get("focus_task", "알 수 없음")
    print(f"✅ 로그 불러오기 완료: {focus_task}")

    # 2. Slack DM으로 회고 요청
    greeting = f"""🌙 하루 고생하셨어요!

오늘 집중했던 '{focus_task}', 어떻게 됐나요?"""

    send_dm(greeting)
    print("✅ 회고 요청 메시지 발송 완료")

    # 3. 사용자 응답 대기
    user_response = wait_for_user_response(timeout_minutes=5)

    if not user_response:
        # 무응답 시
        send_dm("응답이 없어서 회고를 진행하지 못했어요. 그래도 오늘 하루 고생 많으셨어요! 편히 쉬세요 😊")
        return

    # 4. Coach GPT 피드백 요청
    print("\n🧑‍🏫 Coach GPT 피드백 요청 중...")
    reflection_prompt = format_reflection_prompt(log_data, user_response)
    coach_feedback = get_coach_feedback(reflection_prompt)
    print("✅ 피드백 받기 완료")

    # 5. Slack으로 피드백 전달
    print("\n📤 피드백 메시지 발송...")
    feedback_message = format_feedback_message(log_data, user_response, coach_feedback)
    send_dm(feedback_message)

    # 6. 회고 로그 업데이트
    log_data["reflection"] = {
        "user_response": user_response,
        "coach_feedback": coach_feedback,
        "timestamp": datetime.now().isoformat()
    }

    log_dir = Path.home() / ".daily-focus"
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"{today}.json"

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    print(f"💾 회고 로그 업데이트 완료: {log_file}")

    print("\n" + "=" * 60)
    print("✅ 저녁 워크플로우 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
