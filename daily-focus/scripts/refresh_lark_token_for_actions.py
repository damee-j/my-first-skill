#!/usr/bin/env python3
"""
GitHub Actions용 Lark 토큰 자동 갱신 스크립트

Lark User Access Token은 약 2시간마다 만료되므로,
이 스크립트를 GitHub Actions에서 실행 전에 호출하여 토큰을 갱신합니다.

⚠️ 주의: 이 스크립트는 브라우저 없이 작동하지 않습니다.
대신 Tenant Access Token을 사용하거나, 수동으로 GitHub Secrets를 업데이트해야 합니다.
"""

import os
import sys
import requests
from datetime import datetime
import json


def get_tenant_access_token():
    """
    Tenant Access Token 발급 (앱 레벨 토큰)

    User Access Token 대신 사용 가능하지만, 개인 캘린더 접근 불가.
    따라서 daily-focus에는 적합하지 않음.
    """
    app_id = os.getenv('LARK_APP_ID')
    app_secret = os.getenv('LARK_APP_SECRET')

    if not app_id or not app_secret:
        print("❌ LARK_APP_ID 또는 LARK_APP_SECRET이 설정되지 않았습니다.")
        sys.exit(1)

    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": app_id,
        "app_secret": app_secret
    }

    response = requests.post(url, json=payload, timeout=10)

    if response.status_code == 200:
        data = response.json()
        if data.get("code") == 0:
            token = data.get("tenant_access_token")
            print(f"✅ Tenant Access Token 발급 성공")
            print(f"Token: {token[:50]}...")
            return token
        else:
            print(f"❌ API 에러: {data.get('msg')}")
            sys.exit(1)
    else:
        print(f"❌ HTTP {response.status_code}: {response.text}")
        sys.exit(1)


def check_user_token_expiry():
    """현재 User Access Token의 만료 시각 확인"""
    import base64

    token = os.getenv('LARK_USER_TOKEN')
    if not token:
        print("❌ LARK_USER_TOKEN이 설정되지 않았습니다.")
        return None

    try:
        # JWT 디코딩
        parts = token.split('.')
        if len(parts) != 3:
            print("❌ Invalid JWT format")
            return None

        payload = parts[1]
        padding = 4 - (len(payload) % 4)
        if padding != 4:
            payload += '=' * padding

        decoded = base64.urlsafe_b64decode(payload)
        data = json.loads(decoded)

        exp_timestamp = data.get('exp', 0)
        now_timestamp = datetime.now().timestamp()
        remaining_sec = exp_timestamp - now_timestamp

        exp_dt = datetime.fromtimestamp(exp_timestamp)

        print(f"토큰 만료 시각: {exp_dt}")
        print(f"현재 시각: {datetime.now()}")
        print(f"남은 시간: {remaining_sec / 60:.1f}분")

        if remaining_sec < 0:
            print("❌ 토큰 만료됨")
            return "expired"
        elif remaining_sec < 600:  # 10분 미만
            print("⚠️  곧 만료 예정 (10분 미만)")
            return "expiring_soon"
        else:
            print("✅ 토큰 유효")
            return "valid"

    except Exception as e:
        print(f"❌ 토큰 확인 실패: {e}")
        return None


if __name__ == "__main__":
    print("=" * 70)
    print("🔑 Lark Token 상태 확인")
    print("=" * 70)
    print()

    status = check_user_token_expiry()

    print()
    print("=" * 70)
    print("📋 안내")
    print("=" * 70)
    print()
    print("Lark User Access Token은 브라우저 OAuth 인증이 필요하므로,")
    print("GitHub Actions에서 자동 갱신이 불가능합니다.")
    print()
    print("해결 방법:")
    print("1. 로컬에서 `python3 scripts/lark_oauth.py` 실행")
    print("2. 새 토큰을 GitHub Secrets의 LARK_USER_TOKEN에 업데이트")
    print()
    print("또는:")
    print("- 토큰이 만료되면 Slack DM으로 알림 받기 (morning_flow.py가 자동 처리)")
    print()

    if status == "expired":
        print("⚠️  현재 토큰이 만료되었습니다. GitHub Secrets를 업데이트하세요.")
        sys.exit(1)
    elif status == "expiring_soon":
        print("⚠️  토큰이 곧 만료됩니다. 갱신을 권장합니다.")
        sys.exit(0)
    else:
        print("✅ 토큰이 유효합니다. 워크플로우를 계속 진행합니다.")
        sys.exit(0)
