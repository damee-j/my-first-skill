#!/usr/bin/env python3
"""
기존 .env의 LARK_USER_TOKEN을 token manager로 마이그레이션

현재 토큰을 token cache에 저장하여 만료 추적 가능
"""
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import jwt

load_dotenv()

LARK_USER_TOKEN = os.getenv('LARK_USER_TOKEN')
TOKEN_CACHE_FILE = Path.home() / '.daily-focus' / 'lark_tokens.json'


def decode_token_info(token):
    """JWT 토큰 디코드 (서명 검증 없이)"""
    try:
        # JWT 토큰 디코드 (verify=False로 서명 검증 스킵)
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception as e:
        print(f"⚠️ 토큰 디코드 실패: {e}")
        return None


def migrate_token():
    """기존 토큰을 token manager로 마이그레이션"""
    if not LARK_USER_TOKEN:
        print("❌ .env에 LARK_USER_TOKEN이 없습니다.")
        return False

    print(f"📦 현재 토큰: {LARK_USER_TOKEN[:20]}...")

    # 토큰 정보 디코드
    token_info = decode_token_info(LARK_USER_TOKEN)

    if token_info:
        print("\n🔍 토큰 정보:")
        print(f"  - 발급 시간 (iat): {datetime.fromtimestamp(token_info.get('iat', 0))}")
        print(f"  - 만료 시간 (exp): {datetime.fromtimestamp(token_info.get('exp', 0))}")

        if 'auth_exp' in token_info:
            auth_exp = datetime.fromtimestamp(token_info['auth_exp'])
            print(f"  - 인증 만료 (auth_exp): {auth_exp}")
            print(f"  - 남은 시간: {auth_exp - datetime.now()}")

        # 만료 시간 계산
        exp_timestamp = token_info.get('exp', 0)
        auth_exp_timestamp = token_info.get('auth_exp', 0)

        expires_at = datetime.fromtimestamp(exp_timestamp)
        refresh_expires_at = datetime.fromtimestamp(auth_exp_timestamp) if auth_exp_timestamp > 0 else expires_at + timedelta(days=30)

    else:
        # 디코드 실패 시 기본값 사용
        print("\n⚠️ 토큰 정보를 디코드할 수 없습니다. 기본 만료 시간을 사용합니다.")
        expires_at = datetime.now() + timedelta(hours=2)
        refresh_expires_at = datetime.now() + timedelta(days=30)

    # Token cache 저장
    TOKEN_CACHE_FILE.parent.mkdir(exist_ok=True)

    token_data = {
        'access_token': LARK_USER_TOKEN,
        'refresh_token': None,  # Refresh token이 없으므로 None
        'expires_at': expires_at.isoformat(),
        'refresh_expires_at': refresh_expires_at.isoformat(),
        'updated_at': datetime.now().isoformat()
    }

    with open(TOKEN_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(token_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 토큰을 마이그레이션했습니다: {TOKEN_CACHE_FILE}")
    print(f"  - Access Token 만료: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  - 재로그인 필요: {refresh_expires_at.strftime('%Y-%m-%d %H:%M:%S')}")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("🔄 Lark Token Migration")
    print("=" * 60)
    print()

    if migrate_token():
        print("\n✅ 완료!")
    else:
        print("\n❌ 실패!")
