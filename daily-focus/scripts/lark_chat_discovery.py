#!/usr/bin/env python3
"""
Lark 그룹 채팅 ID 조회 스크립트

봇이 참여한 그룹 채팅 목록을 조회하여 chat_id를 찾는다.
찾은 chat_id를 .env 파일의 LARK_CHAT_ID에 저장.

사용법:
    python3 scripts/lark_chat_discovery.py
"""

import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
sys.path.insert(0, str(Path(__file__).parent))

from lark_tenant_token import get_valid_tenant_token

BASE_URL = "https://open.larksuite.com/open-apis"


def list_bot_chats():
    """봇이 참여한 채팅 목록 조회"""
    token = get_valid_tenant_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"{BASE_URL}/im/v1/chats"
    response = requests.get(url, headers=headers)
    data = response.json()

    if data.get("code") != 0:
        print(f"❌ 채팅 목록 조회 실패: {data.get('msg')}")
        return []

    chats = data.get("data", {}).get("items", [])
    return chats


def save_chat_id_to_env(chat_id: str):
    """chat_id를 .env 파일에 저장"""
    env_path = Path(__file__).parent.parent / ".env"

    if not env_path.exists():
        print(f"❌ .env 파일이 없습니다: {env_path}")
        return False

    content = env_path.read_text(encoding="utf-8")

    if "LARK_CHAT_ID=" in content:
        lines = content.split("\n")
        new_lines = []
        for line in lines:
            if line.startswith("LARK_CHAT_ID="):
                new_lines.append(f"LARK_CHAT_ID={chat_id}")
            else:
                new_lines.append(line)
        content = "\n".join(new_lines)
    else:
        content += f"\nLARK_CHAT_ID={chat_id}\n"

    env_path.write_text(content, encoding="utf-8")
    print(f"✅ LARK_CHAT_ID={chat_id} → .env 저장 완료")
    return True


def main():
    print("=" * 60)
    print("🔍 Lark 봇 채팅 목록 조회")
    print("=" * 60)

    chats = list_bot_chats()

    if not chats:
        print("\n봇이 참여한 채팅이 없습니다.")
        print("Lark에서 그룹을 만들고 봇을 초대해주세요.")
        return

    print(f"\n📋 봇이 참여한 채팅 ({len(chats)}개):\n")
    for i, chat in enumerate(chats, 1):
        chat_id = chat.get("chat_id", "")
        name = chat.get("name", "(이름 없음)")
        chat_type = chat.get("chat_type", "")
        owner_id = chat.get("owner_id", "")
        print(f"  {i}. {name}")
        print(f"     chat_id: {chat_id}")
        print(f"     type: {chat_type}")
        print()

    # 하나만 있으면 자동 선택
    if len(chats) == 1:
        selected = chats[0]
        print(f"✅ 채팅이 1개뿐이므로 자동 선택: {selected.get('name')}")
        save_chat_id_to_env(selected["chat_id"])
        return

    # 여러 개면 선택
    try:
        choice = input("사용할 채팅 번호를 입력하세요: ").strip()
        idx = int(choice) - 1
        if 0 <= idx < len(chats):
            selected = chats[idx]
            save_chat_id_to_env(selected["chat_id"])
        else:
            print("❌ 잘못된 번호입니다.")
    except (ValueError, EOFError):
        print("❌ 입력이 올바르지 않습니다.")


if __name__ == "__main__":
    main()
