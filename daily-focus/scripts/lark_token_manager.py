#!/usr/bin/env python3
"""
Lark Token 자동 갱신 관리자

- Access token이 만료되면 refresh token으로 자동 갱신
- Refresh token도 만료되면 재로그인 안내
"""
import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

LARK_APP_ID = os.getenv('LARK_APP_ID')
LARK_APP_SECRET = os.getenv('LARK_APP_SECRET')

# 토큰 정보 저장 파일
TOKEN_CACHE_FILE = Path.home() / '.daily-focus' / 'lark_tokens.json'


def load_tokens():
    """저장된 토큰 정보 불러오기"""
    if not TOKEN_CACHE_FILE.exists():
        return None

    try:
        with open(TOKEN_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def save_tokens(access_token, refresh_token, expires_in, refresh_expires_in):
    """토큰 정보 저장"""
    TOKEN_CACHE_FILE.parent.mkdir(exist_ok=True)

    token_data = {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_at': (datetime.now() + timedelta(seconds=expires_in - 300)).isoformat(),  # 5분 여유
        'refresh_expires_at': (datetime.now() + timedelta(seconds=refresh_expires_in - 3600)).isoformat(),  # 1시간 여유
        'updated_at': datetime.now().isoformat()
    }

    with open(TOKEN_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(token_data, f, indent=2)

    # .env 파일도 업데이트
    update_env_file(access_token)

    return token_data


def update_env_file(access_token):
    """env 파일의 LARK_USER_TOKEN 업데이트"""
    env_file = Path(__file__).parent.parent / '.env'

    if not env_file.exists():
        return

    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    token_line = f"LARK_USER_TOKEN={access_token}\n"
    updated = False

    for i, line in enumerate(lines):
        if line.startswith('LARK_USER_TOKEN='):
            lines[i] = token_line
            updated = True
            break

    if not updated:
        lines.append(token_line)

    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def refresh_access_token(refresh_token):
    """Refresh token으로 새 access token 발급"""
    url = "https://open.larksuite.com/open-apis/authen/v2/oauth/token"

    payload = {
        "grant_type": "refresh_token",
        "client_id": LARK_APP_ID,
        "client_secret": LARK_APP_SECRET,
        "refresh_token": refresh_token
    }

    response = requests.post(url, json=payload)
    result = response.json()

    if result.get('code') == 0:
        data = result.get('data', {})
        return {
            'access_token': data.get('access_token'),
            'refresh_token': data.get('refresh_token'),
            'expires_in': data.get('expires_in', 7200),  # 기본 2시간
            'refresh_expires_in': data.get('refresh_expires_in', 604800)  # 기본 7일
        }
    else:
        raise Exception(f"토큰 갱신 실패: {result.get('msg')}")


def get_valid_token():
    """유효한 access token 반환 (필요시 자동 갱신)"""
    token_data = load_tokens()

    if not token_data:
        # GitHub Actions 등 캐시 파일이 없는 환경: 환경변수로 폴백
        refresh_token_env = os.getenv('LARK_REFRESH_TOKEN')
        if refresh_token_env:
            print("🔄 환경변수 LARK_REFRESH_TOKEN으로 토큰 갱신 중...")
            try:
                new_tokens = refresh_access_token(refresh_token_env)
                save_tokens(
                    new_tokens['access_token'],
                    new_tokens['refresh_token'],
                    new_tokens['expires_in'],
                    new_tokens['refresh_expires_in']
                )
                print("✅ 토큰 갱신 완료")
                return new_tokens['access_token']
            except Exception as e:
                print(f"❌ LARK_REFRESH_TOKEN 갱신 실패: {e}")

        print("❌ 저장된 토큰이 없습니다.")
        print("python3 scripts/lark_oauth.py를 실행하여 로그인해주세요.")
        return None

    # Access token 만료 확인
    expires_at = datetime.fromisoformat(token_data['expires_at'])

    if datetime.now() < expires_at:
        # 아직 유효함
        return token_data['access_token']

    # Access token이 만료됨
    print("⚠️ Access token이 만료되었습니다.")

    # Refresh token이 있는지 확인
    if not token_data.get('refresh_token'):
        print("❌ Refresh token이 없습니다.")
        print("python3 scripts/lark_oauth.py를 실행하여 다시 로그인해주세요.")
        return None

    # Refresh token 만료 확인
    refresh_expires_at = datetime.fromisoformat(token_data['refresh_expires_at'])

    if datetime.now() >= refresh_expires_at:
        print("❌ Refresh token도 만료되었습니다.")
        print("python3 scripts/lark_oauth.py를 실행하여 다시 로그인해주세요.")
        return None

    # Refresh token으로 갱신 시도
    print("🔄 Refresh token으로 갱신 중...")

    try:
        # Refresh token으로 새 토큰 발급
        new_tokens = refresh_access_token(token_data['refresh_token'])

        # 새 토큰 저장
        save_tokens(
            new_tokens['access_token'],
            new_tokens['refresh_token'],
            new_tokens['expires_in'],
            new_tokens['refresh_expires_in']
        )

        print(f"✅ 토큰 갱신 완료 (다음 만료: {datetime.now() + timedelta(seconds=new_tokens['expires_in'])})")

        return new_tokens['access_token']

    except Exception as e:
        print(f"❌ 토큰 갱신 실패: {e}")
        print("python3 scripts/lark_oauth.py를 실행하여 다시 로그인해주세요.")
        return None


def main():
    """테스트용 메인 함수"""
    print("=" * 60)
    print("🔐 Lark Token Manager")
    print("=" * 60)

    token = get_valid_token()

    if token:
        print(f"\n✅ 유효한 Access Token: {token[:20]}...")

        # 토큰 정보 출력
        token_data = load_tokens()
        if token_data:
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            refresh_expires_at = datetime.fromisoformat(token_data['refresh_expires_at'])

            print(f"\n📅 토큰 만료 정보:")
            print(f"  - Access Token 만료: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  - Refresh Token 만료: {refresh_expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("\n❌ 유효한 토큰을 가져올 수 없습니다.")


if __name__ == "__main__":
    main()
