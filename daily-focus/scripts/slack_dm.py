#!/usr/bin/env python3
"""
Slack DM 발송 스크립트

사용법:
    python3 slack_dm.py "메시지 내용"
    python3 slack_dm.py --interactive  # 대화형 모드
"""

import os
import sys
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_USER_ID = os.getenv("SLACK_USER_ID")
SLACK_CHANNEL_NAME = os.getenv("SLACK_CHANNEL_NAME", "daily-focus")  # 기본값: daily-focus
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")  # 채널 ID 우선 사용

if not SLACK_BOT_TOKEN:
    print("❌ 환경변수가 설정되지 않았습니다.")
    print("SLACK_BOT_TOKEN을 .env 파일에 설정해주세요.")
    sys.exit(1)

client = WebClient(token=SLACK_BOT_TOKEN)


def send_dm(message: str, use_channel: bool = True) -> bool:
    """Slack 메시지 발송 (채널 또는 DM)"""
    try:
        # 채널 또는 DM 선택 (채널 ID 우선 사용)
        if use_channel:
            channel = SLACK_CHANNEL_ID if SLACK_CHANNEL_ID else SLACK_CHANNEL_NAME
        else:
            channel = SLACK_USER_ID

        response = client.chat_postMessage(
            channel=channel,
            text=message
        )

        if response["ok"]:
            target = f"#{SLACK_CHANNEL_NAME}" if use_channel else "DM"
            print(f"✅ {target} 발송 성공: {message[:50]}...")
            return True
        else:
            print(f"❌ 메시지 발송 실패: {response}")
            return False

    except SlackApiError as e:
        print(f"❌ Slack API 오류: {e.response['error']}")
        return False


def get_recent_messages(limit: int = 10, use_channel: bool = True) -> list:
    """최근 메시지 조회 (채널 또는 DM)"""
    try:
        if use_channel:
            # 채널에서 메시지 조회 (채널 ID 우선 사용)
            channel = SLACK_CHANNEL_ID if SLACK_CHANNEL_ID else SLACK_CHANNEL_NAME
            history = client.conversations_history(
                channel=channel,
                limit=limit
            )
        else:
            # DM 채널 ID 확인
            response = client.conversations_open(users=[SLACK_USER_ID])
            channel_id = response["channel"]["id"]

            # 메시지 조회
            history = client.conversations_history(
                channel=channel_id,
                limit=limit
            )

        messages = []
        for msg in history["messages"]:
            if "text" in msg:
                messages.append({
                    "text": msg["text"],
                    "timestamp": msg["ts"],
                    "user": msg.get("user", "bot")
                })

        return messages

    except SlackApiError as e:
        print(f"❌ 메시지 조회 실패: {e.response['error']}")
        return []


def interactive_mode():
    """대화형 모드"""
    print("🤖 Slack DM 대화형 모드 (종료: 'exit')")
    print("-" * 50)

    while True:
        user_input = input("\n💬 메시지: ").strip()

        if user_input.lower() in ["exit", "quit", "종료"]:
            print("👋 종료합니다.")
            break

        if not user_input:
            continue

        send_dm(user_input)


def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python3 slack_dm.py \"메시지 내용\"")
        print("  python3 slack_dm.py --interactive")
        print("  python3 slack_dm.py --recent")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--interactive":
        interactive_mode()
    elif arg == "--recent":
        print("📨 최근 메시지:")
        messages = get_recent_messages()
        for i, msg in enumerate(messages, 1):
            user = "봇" if msg["user"] == "bot" else "나"
            print(f"{i}. [{user}] {msg['text']}")
    else:
        # 일반 메시지 발송
        message = " ".join(sys.argv[1:])
        send_dm(message)


if __name__ == "__main__":
    main()
