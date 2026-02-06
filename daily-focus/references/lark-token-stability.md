# Lark OAuth 토큰 안정성 가이드

## 문제점

Lark User Access Token의 경우:
- **유효기간: 2시간** ⏰
- 만료되면 수동으로 재로그인 필요
- daily-focus 스킬이 자동 실행 중 토큰이 만료되면 실패

## 해결 방법

### ✅ 방법 1: Refresh Token 활용 (추천 - 개인 캘린더 접근)

User OAuth 방식을 유지하면서 refresh token으로 자동 갱신합니다.

**장점**:
- 개인 캘린더에 직접 접근 가능
- 30일간 자동 갱신 (재로그인 불필요)
- 보안성 유지

**단점**:
- Lark API v2에서는 refresh token을 제공하지 않을 수 있음
- 30일마다 한 번은 재로그인 필요

**사용법**:
```bash
# 1. OAuth 로그인 (refresh token 포함)
python3 scripts/lark_oauth.py

# 2. 스크립트에서 자동으로 토큰 갱신
python3 scripts/lark_token_manager.py
```

**구현 완료**:
- `lark_token_manager.py`: 토큰 자동 갱신 관리자
- `lark_oauth.py`: refresh token 저장 지원
- `lark_calendar.py`: token manager 사용으로 자동 갱신

### ✅ 방법 2: Tenant Access Token (추천 - 공유 캘린더/봇 계정)

App 권한으로 토큰을 발급받아 자동으로 갱신합니다.

**장점**:
- **완전 자동화**: 사용자 로그인 불필요
- **무제한 자동 갱신**: 2시간마다 자동으로 갱신
- **안정성 최고**: 토큰 만료 걱정 없음

**단점**:
- 개인 캘린더가 아닌 봇 계정 또는 공유 캘린더만 접근 가능
- 봇을 캘린더 멤버로 추가해야 함

**사용법**:
```bash
# 자동으로 토큰 발급/갱신 (로그인 불필요)
python3 scripts/lark_tenant_token.py
```

**Lark 설정 필요**:
1. Lark Admin Console → 앱 설정
2. 권한 탭 → "calendar:calendar" 권한 활성화
3. 캘린더 앱 → 설정 → 봇 추가
4. 봇 계정에 캘린더 편집 권한 부여

### 방법 3: Lark Bot Token (현재 사용 중)

`LARK_BOT_TOKEN`을 사용하는 방식입니다.

**장점**:
- 설정이 간단
- 토큰이 비교적 오래 유지됨

**단점**:
- 캘린더 API 접근 권한이 제한적
- 개인 캘린더 접근 불가능할 수 있음

## 권장 설정

### 🚀 최종 추천: Refresh Token + Fallback

1. **기본**: Refresh Token 방식 사용 (개인 캘린더 접근)
2. **Fallback**: 30일마다 재로그인 필요 시 알림

**설정 방법**:

```bash
# 1. 초기 로그인
python3 scripts/lark_oauth.py
# → refresh token이 저장됨

# 2. 이후 자동 갱신
python3 scripts/lark_calendar.py --list-events
# → 토큰이 만료되었으면 자동으로 refresh token으로 갱신

# 3. 30일마다 한 번씩 재로그인
python3 scripts/lark_oauth.py
```

**cron job 설정**:

```bash
# 매월 1일에 자동으로 재로그인 (알림만)
0 9 1 * * echo "⚠️ Lark 토큰 갱신이 필요합니다. python3 scripts/lark_oauth.py를 실행해주세요." | mail -s "daily-focus 토큰 갱신" your-email@example.com
```

## 토큰 상태 확인

```bash
# Token manager 상태 확인
python3 scripts/lark_token_manager.py

# 출력 예시:
# ✅ 유효한 Access Token: eyJhbGciOiJFUzI1NiIs...
#
# 📅 토큰 만료 정보:
#   - Access Token 만료: 2026-02-06 18:58:42
#   - Refresh Token 만료: 2026-03-08 16:58:42
```

## 문제 해결

### 1. "토큰이 만료되었습니다" 에러

```bash
# 해결: 재로그인
python3 scripts/lark_oauth.py
```

### 2. "Refresh token도 만료되었습니다" 에러

```bash
# 해결: 완전히 새로 로그인
python3 scripts/lark_oauth.py
```

### 3. "no calendar access_role" 에러

- User Token 권한 부족
- 해결: 다시 로그인하거나 Tenant Token 방식 사용

## 자동화 설정

### Morning/Evening Flow에 토큰 체크 추가

`morning_flow.py` 및 `evening_flow.py`는 자동으로 token manager를 사용하므로:

- ✅ 토큰이 만료되면 자동으로 refresh
- ✅ Refresh token도 만료되었으면 에러 로그 남기고 Slack 알림

**알림 추가 (선택)**:

```python
# morning_flow.py에 추가
from lark_token_manager import get_valid_token

token = get_valid_token()
if not token:
    send_dm("⚠️ Lark 토큰이 만료되었습니다. 재로그인이 필요해요!\npython3 scripts/lark_oauth.py")
    sys.exit(1)
```

## 요약

| 방식 | 자동 갱신 | 개인 캘린더 | 설정 복잡도 | 추천도 |
|------|-----------|-------------|-------------|--------|
| Refresh Token | 30일 | ✅ | 중간 | ⭐⭐⭐⭐⭐ |
| Tenant Token | 무제한 | ❌ (공유만) | 낮음 | ⭐⭐⭐⭐ |
| Bot Token | 장기 | ❌ | 낮음 | ⭐⭐⭐ |

**결론**: **Refresh Token 방식**을 사용하되, 30일마다 재로그인하는 것이 가장 안정적입니다.
