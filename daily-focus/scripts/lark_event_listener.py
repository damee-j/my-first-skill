#!/usr/bin/env python3
"""
Lark 그룹 채팅 메시지 폴링

그룹 채팅의 최근 메시지를 주기적으로 조회하여 사용자 응답을 감지.
Tenant Access Token 사용.

인터페이스:
    start_listener()      — 봇 메시지 발송 시각 기록 (폴링 기준점)
    wait_for_message()    — 기준점 이후 사용자 메시지를 폴링하여 반환
    clear_queue()         — 기준 시각 리셋

사용법:
    # nightly_flow.py에서 사용
    from lark_event_listener import start_listener, wait_for_message, clear_queue
"""

import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from lark_tenant_token import get_valid_tenant_token

LARK_CHAT_ID = os.getenv("LARK_CHAT_ID")
LARK_APP_ID = os.getenv("LARK_APP_ID")

BASE_URL = "https://open.larksuite.com/open-apis"

# 폴링 기준 시각 (이 시각 이후의 메시지만 수신)
_baseline_timestamp = None


def _get_headers():
    """인증 헤더 생성"""
    token = get_valid_tenant_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


def _get_bot_app_id():
    """봇 앱 ID 반환 (봇 메시지 필터링용)"""
    return LARK_APP_ID


def _fetch_recent_messages(start_time: str, page_size: int = 20):
    """그룹 채팅의 최근 메시지 조회

    Args:
        start_time: Unix timestamp (초 단위, 문자열)
        page_size: 조회할 메시지 수

    Returns:
        list: 메시지 목록 (최신 순)
    """
    url = f"{BASE_URL}/im/v1/messages"
    params = {
        "container_id_type": "chat",
        "container_id": LARK_CHAT_ID,
        "start_time": start_time,
        "sort_type": "ByCreateTimeDesc",
        "page_size": str(page_size),
    }

    try:
        response = requests.get(url, headers=_get_headers(), params=params)
        data = response.json()

        if data.get("code") != 0:
            print(f"❌ 메시지 조회 실패: {data.get('msg')}")
            return []

        items = data.get("data", {}).get("items", [])
        return items
    except Exception as e:
        print(f"❌ 메시지 조회 오류: {e}")
        return []


def _extract_text_from_post(content):
    """post 타입 메시지에서 텍스트 추출

    post content 구조: {"title": "", "content": [[{tag, text}, ...], ...]}
    각 줄의 text 태그를 이어붙여 반환.
    """
    lines = []
    for paragraph in content.get("content", []):
        line_parts = []
        for element in paragraph:
            if element.get("tag") == "text":
                line_parts.append(element.get("text", ""))
        line = "".join(line_parts).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def _find_user_message(messages):
    """메시지 목록에서 사용자(봇이 아닌) 텍스트 메시지를 찾기

    text 타입과 post 타입(리치 텍스트) 모두 처리.

    Returns:
        str: 사용자 메시지 텍스트, 없으면 None
    """
    for msg in messages:
        sender = msg.get("sender", {})
        sender_type = sender.get("sender_type", "")

        # 봇 메시지 건너뛰기 (app 타입)
        if sender_type == "app":
            continue

        msg_type = msg.get("msg_type", "")
        body = msg.get("body", {})

        try:
            content = json.loads(body.get("content", "{}"))

            if msg_type == "text":
                text = content.get("text", "").strip()
                if text:
                    return text
            elif msg_type == "post":
                text = _extract_text_from_post(content)
                if text:
                    return text
        except (json.JSONDecodeError, AttributeError):
            continue

    return None


def start_listener() -> None:
    """폴링 기준 시각 설정 (현재 시각)"""
    global _baseline_timestamp
    _baseline_timestamp = str(int(time.time()))
    print("🔌 그룹 채팅 메시지 폴링 준비 완료")


def wait_for_message(timeout_minutes: int = 5):
    """그룹 채팅을 폴링하여 사용자 메시지 대기

    Args:
        timeout_minutes: 최대 대기 시간 (분)

    Returns:
        str: 수신된 메시지 텍스트, 타임아웃 시 None
    """
    global _baseline_timestamp

    if not LARK_CHAT_ID:
        print("❌ LARK_CHAT_ID가 설정되지 않았습니다.")
        return None

    if not _baseline_timestamp:
        _baseline_timestamp = str(int(time.time()))

    print(f"⏳ 사용자 응답 대기 중... (최대 {timeout_minutes}분)")

    poll_interval = 5  # 5초마다 폴링
    deadline = time.time() + (timeout_minutes * 60)

    while time.time() < deadline:
        messages = _fetch_recent_messages(_baseline_timestamp)

        user_text = _find_user_message(messages)
        if user_text:
            print(f"✅ 응답 받음: {user_text[:50]}...")
            # 다음 폴링 기준점 업데이트
            _baseline_timestamp = str(int(time.time()))
            return user_text

        time.sleep(poll_interval)

    print("⏰ 타임아웃: 응답이 없습니다.")
    return None


def clear_queue() -> None:
    """폴링 기준 시각을 현재로 리셋 (새 질문 전 호출)"""
    global _baseline_timestamp
    _baseline_timestamp = str(int(time.time()))


if __name__ == "__main__":
    print("=" * 60)
    print("🔍 Lark 그룹 채팅 메시지 폴링 테스트")
    print("=" * 60)
    print("그룹에서 메시지를 보내보세요.")
    print("Ctrl+C로 종료.\n")

    start_listener()

    try:
        while True:
            msg = wait_for_message(timeout_minutes=1)
            if msg:
                print(f"\n💬 수신: {msg}\n")
            else:
                print("(타임아웃, 다시 대기...)\n")
    except KeyboardInterrupt:
        print("\n👋 종료합니다.")
