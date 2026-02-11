#!/usr/bin/env python3
"""
Lark OAuth 2.0 로그인 및 캘린더 조회
"""
import os
import json
import webbrowser
import secrets
import hashlib
import base64
from urllib.parse import urlencode, parse_qs, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

LARK_APP_ID = os.getenv('LARK_APP_ID')
LARK_APP_SECRET = os.getenv('LARK_APP_SECRET')
REDIRECT_URI = "http://localhost:8080/callback"

# PKCE를 위한 code verifier와 challenge 생성
def generate_pkce():
    """PKCE code verifier와 challenge 생성"""
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge

# 전역 변수로 OAuth 상태 관리
oauth_state = {
    'state': secrets.token_urlsafe(16),
    'code_verifier': None,
    'code_challenge': None,
    'authorization_code': None,
    'access_token': None
}

# PKCE 생성
oauth_state['code_verifier'], oauth_state['code_challenge'] = generate_pkce()

class OAuthHandler(BaseHTTPRequestHandler):
    """OAuth callback 처리 핸들러"""

    def log_message(self, format, *args):
        """로그 메시지 비활성화"""
        pass

    def do_GET(self):
        """GET 요청 처리"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/callback':
            # 쿼리 파라미터 파싱
            query_params = parse_qs(parsed_path.query)

            # State 검증
            received_state = query_params.get('state', [''])[0]
            if received_state != oauth_state['state']:
                self.send_error(400, "Invalid state parameter")
                return

            # Authorization code 저장
            oauth_state['authorization_code'] = query_params.get('code', [''])[0]

            if oauth_state['authorization_code']:
                # 성공 페이지 표시
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()

                html = """
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                        .success { color: green; font-size: 24px; }
                    </style>
                </head>
                <body>
                    <div class="success">✅ 로그인 성공!</div>
                    <p>이제 이 창을 닫으셔도 됩니다.</p>
                </body>
                </html>
                """
                self.wfile.write(html.encode())
            else:
                self.send_error(400, "Authorization failed")
        else:
            self.send_error(404, "Not found")

def get_authorization_url():
    """Authorization URL 생성"""
    params = {
        'client_id': LARK_APP_ID,
        'redirect_uri': REDIRECT_URI,
        'state': oauth_state['state'],
        'code_challenge': oauth_state['code_challenge'],
        'code_challenge_method': 'S256',
        'scope': 'calendar:calendar offline_access'  # 캘린더 권한 + refresh token 발급
    }

    base_url = "https://open.larksuite.com/open-apis/authen/v1/authorize"
    return f"{base_url}?{urlencode(params)}"

def exchange_code_for_token(code):
    """Authorization code를 access token으로 교환"""
    url = "https://open.larksuite.com/open-apis/authen/v2/oauth/token"

    payload = {
        "grant_type": "authorization_code",
        "client_id": LARK_APP_ID,
        "client_secret": LARK_APP_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": oauth_state['code_verifier']
    }

    response = requests.post(url, json=payload)
    result = response.json()

    if result.get('code') == 0:
        # data 객체가 있는지 확인
        if 'data' in result:
            data = result['data']
            return {
                'access_token': data.get('access_token'),
                'refresh_token': data.get('refresh_token'),
                'expires_in': data.get('expires_in', 7200),
                'refresh_expires_in': data.get('refresh_expires_in', 2592000)
            }
        else:
            # 구버전 API 응답 (data 없이 바로 반환)
            return {
                'access_token': result.get('access_token'),
                'refresh_token': result.get('refresh_token'),
                'expires_in': result.get('expires_in', 7200),
                'refresh_expires_in': result.get('refresh_expires_in', 2592000)
            }
    else:
        raise Exception(f"토큰 교환 실패: {result}")

def get_user_calendars(user_token):
    """사용자의 캘린더 목록 조회"""
    url = "https://open.larksuite.com/open-apis/calendar/v4/calendars"
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    response = requests.get(url, headers=headers)
    return response.json()

def get_calendar_events(user_token, calendar_id):
    """캘린더 이벤트 조회"""
    from datetime import datetime, timedelta

    start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=30)

    start_ts = str(int(start_time.timestamp()))
    end_ts = str(int(end_time.timestamp()))

    url = f"https://open.larksuite.com/open-apis/calendar/v4/calendars/{calendar_id}/events"
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    params = {
        "start_time": start_ts,
        "end_time": end_ts,
        "page_size": 100
    }

    response = requests.get(url, headers=headers, params=params)
    return response.json()

def format_timestamp(ts):
    """Unix timestamp를 읽기 쉬운 형식으로 변환"""
    from datetime import datetime
    if not ts:
        return "시간 정보 없음"
    try:
        dt = datetime.fromtimestamp(int(ts))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return ts

def format_event(event):
    """이벤트를 보기 좋게 포맷팅"""
    summary = event.get('summary', '(제목 없음)')
    start = event.get('start_time', {})
    end = event.get('end_time', {})

    # 시간 포맷팅
    start_ts = start.get('timestamp', '')
    end_ts = end.get('timestamp', '')

    start_str = format_timestamp(start_ts)
    end_str = format_timestamp(end_ts)

    return f"• {summary}\n  📅 {start_str} ~ {end_str}"

def main():
    print("=" * 60)
    print("🔐 Lark OAuth 로그인")
    print("=" * 60)

    # 1. Authorization URL 생성
    auth_url = get_authorization_url()
    print(f"\n📱 브라우저에서 Lark 로그인을 진행합니다...")
    print(f"\n만약 브라우저가 자동으로 열리지 않으면, 아래 URL을 복사해서 브라우저에 붙여넣으세요:")
    print(f"\n{auth_url}\n")

    # 2. 로컬 서버 시작
    server = HTTPServer(('localhost', 8080), OAuthHandler)
    print("🌐 로컬 서버 시작 (http://localhost:8080)")

    # 3. 브라우저 열기
    webbrowser.open(auth_url)

    # 4. Callback 대기
    print("\n⏳ 로그인 완료를 기다리는 중...\n")
    server.handle_request()  # 한 번의 요청만 처리

    # 5. Authorization code 확인
    if not oauth_state['authorization_code']:
        print("❌ 로그인 실패")
        return

    print("✅ Authorization code 받음")

    # 6. Access token 교환
    print("\n🔑 Access token 발급 중...")
    token_data = exchange_code_for_token(oauth_state['authorization_code'])
    oauth_state['access_token'] = token_data['access_token']

    print(f"✅ Access token: {token_data['access_token'][:20]}...")

    if token_data.get('refresh_token'):
        print(f"✅ Refresh token: {token_data['refresh_token'][:20]}...")
        print(f"✅ Access token 유효기간: {token_data['expires_in']}초 ({token_data['expires_in']/3600:.1f}시간)")
        print(f"✅ Refresh token 유효기간: {token_data['refresh_expires_in']}초 ({token_data['refresh_expires_in']/86400:.0f}일)")

        # 토큰을 token manager로 저장
        from lark_token_manager import save_tokens
        save_tokens(
            token_data['access_token'],
            token_data['refresh_token'],
            token_data['expires_in'],
            token_data['refresh_expires_in']
        )
        print(f"\n💾 토큰을 .env 파일과 캐시에 저장했습니다 (자동 갱신 지원)")
    else:
        print(f"⚠️  Refresh token을 받지 못했습니다. Access token만 저장합니다.")
        print(f"⚠️  토큰이 만료되면 다시 로그인해야 합니다.")

        # .env 파일만 업데이트
        env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        token_line = f"LARK_USER_TOKEN={token_data['access_token']}\n"
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

        print(f"\n💾 토큰을 .env 파일에 저장했습니다")

    # 7. 캘린더 목록 조회
    print("\n📅 캘린더 목록 조회 중...")
    calendars = get_user_calendars(token_data['access_token'])

    if calendars.get('code') == 0:
        calendar_list = calendars.get('data', {}).get('calendar_list', [])
        print(f"\n발견된 캘린더: {len(calendar_list)}개\n")

        # 8. 각 캘린더의 이벤트 조회
        for cal in calendar_list:
            calendar_id = cal.get('calendar_id')
            calendar_name = cal.get('summary', '이름 없음')
            cal_type = cal.get('type', 'unknown')

            print(f"\n{'=' * 60}")
            print(f"📅 {calendar_name} ({cal_type})")
            print(f"ID: {calendar_id}")
            print(f"{'=' * 60}")

            events_result = get_calendar_events(token_data['access_token'], calendar_id)

            if events_result.get('code') == 0:
                events = events_result.get('data', {}).get('items', [])

                if events:
                    print(f"\n📆 향후 30일간의 일정 ({len(events)}개):\n")
                    for event in events:
                        print(format_event(event))
                        print()
                else:
                    print("\n📭 일정이 없습니다.\n")
            else:
                print(f"\n❌ 이벤트 조회 실패: {events_result.get('msg')}\n")
    else:
        print(f"❌ 캘린더 조회 실패: {calendars}")

    print("\n" + "=" * 60)
    print("✅ 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()
