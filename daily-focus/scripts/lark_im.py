#!/usr/bin/env python3
"""
Lark IM 메시지 발송 스크립트

Lark 메신저를 통해 봇이 그룹 채팅에 메시지를 보낸다.
Tenant Access Token (봇 레벨) 사용.
메시지 수신은 lark_event_listener.py (그룹 채팅 폴링) 담당.

사용법:
    python3 lark_im.py "메시지 내용"
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

from lark_tenant_token import get_valid_tenant_token

LARK_CHAT_ID = os.getenv("LARK_CHAT_ID")

if not LARK_CHAT_ID:
    print("❌ 환경변수가 설정되지 않았습니다.")
    print("LARK_CHAT_ID를 .env 파일에 설정해주세요.")
    print("조회 방법: python3 scripts/lark_chat_discovery.py")
    sys.exit(1)

BASE_URL = "https://open.larksuite.com/open-apis"


def _get_headers():
    """인증 헤더 생성"""
    token = get_valid_tenant_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8"
    }


def _strip_markdown(message: str) -> str:
    """**bold** 마크다운을 plain text로 변환"""
    return message.replace("**", "")


def send_message(message: str) -> bool:
    """Lark IM으로 그룹 채팅에 메시지 발송 (봇 → 그룹)"""
    try:
        url = f"{BASE_URL}/im/v1/messages?receive_id_type=chat_id"
        headers = _get_headers()

        # **bold** 마크다운 제거
        clean_message = _strip_markdown(message)

        payload = {
            "receive_id": LARK_CHAT_ID,
            "msg_type": "text",
            "content": json.dumps({"text": clean_message})
        }

        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        if data.get("code") != 0:
            print(f"❌ 메시지 발송 실패: {data.get('msg')}")
            return False

        print(f"✅ Lark 메시지 발송 성공: {clean_message[:50]}...")
        return True

    except Exception as e:
        print(f"❌ Lark IM 오류: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python3 lark_im.py \"메시지 내용\"")
        sys.exit(1)

    message = " ".join(sys.argv[1:])
    send_message(message)
