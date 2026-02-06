#!/usr/bin/env python3
"""
Lark Tenant Access Token 관리자

User Token 대신 Tenant Access Token 방식 사용:
- App ID와 App Secret만으로 토큰 발급
- 자동으로 2시간마다 갱신 가능
- 사용자 OAuth 로그인 불필요

⚠️ 제한사항:
- 개인 캘린더가 아닌 봇 계정의 권한으로 접근
- 캘린더 이벤트 생성/조회 시 봇 계정 또는 공유된 캘린더만 접근 가능
"""
import os
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

LARK_APP_ID = os.getenv('LARK_APP_ID')
LARK_APP_SECRET = os.getenv('LARK_APP_SECRET')

# 토큰 캐시 파일
TOKEN_CACHE_FILE = Path.home() / '.daily-focus' / 'tenant_token.json'


def get_tenant_access_token():
    """Tenant Access Token 발급"""
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"

    payload = {
        "app_id": LARK_APP_ID,
        "app_secret": LARK_APP_SECRET
    }

    response = requests.post(url, json=payload)
    result = response.json()

    if result.get('code') == 0:
        return {
            'token': result.get('tenant_access_token'),
            'expires_in': result.get('expire', 7200)  # 기본 2시간
        }
    else:
        raise Exception(f"Tenant token 발급 실패: {result}")


def load_cached_token():
    """캐시된 토큰 불러오기"""
    if not TOKEN_CACHE_FILE.exists():
        return None

    try:
        with open(TOKEN_CACHE_FILE, 'r', encoding='utf-8') as f:
            token_data = json.load(f)

        expires_at = datetime.fromisoformat(token_data['expires_at'])

        # 아직 유효한지 확인 (5분 여유)
        if datetime.now() < expires_at:
            return token_data['token']

        return None
    except:
        return None


def save_token(token, expires_in):
    """토큰 캐시 저장"""
    TOKEN_CACHE_FILE.parent.mkdir(exist_ok=True)

    token_data = {
        'token': token,
        'expires_at': (datetime.now() + timedelta(seconds=expires_in - 300)).isoformat(),  # 5분 여유
        'updated_at': datetime.now().isoformat()
    }

    with open(TOKEN_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(token_data, f, indent=2)


def get_valid_tenant_token():
    """유효한 Tenant Access Token 반환 (필요시 자동 발급/갱신)"""
    # 1. 캐시에서 먼저 확인
    cached_token = load_cached_token()
    if cached_token:
        return cached_token

    # 2. 새로 발급
    print("🔄 Tenant Access Token 발급 중...")
    token_data = get_tenant_access_token()

    # 3. 캐시 저장
    save_token(token_data['token'], token_data['expires_in'])

    print(f"✅ Tenant Access Token 발급 완료 (유효기간: {token_data['expires_in']/3600:.1f}시간)")

    return token_data['token']


def main():
    """테스트용 메인 함수"""
    print("=" * 60)
    print("🔐 Lark Tenant Access Token Manager")
    print("=" * 60)

    try:
        token = get_valid_tenant_token()
        print(f"\n✅ Tenant Access Token: {token[:20]}...")

        # 토큰 정보 출력
        if TOKEN_CACHE_FILE.exists():
            with open(TOKEN_CACHE_FILE, 'r', encoding='utf-8') as f:
                token_data = json.load(f)
                expires_at = datetime.fromisoformat(token_data['expires_at'])
                print(f"\n📅 토큰 만료: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"\n❌ 오류: {e}")


if __name__ == "__main__":
    main()
