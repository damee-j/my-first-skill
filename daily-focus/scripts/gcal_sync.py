#!/usr/bin/env python3
"""
Google Calendar → Lark Calendar 동기화 스크립트

Google Calendar 일정을 Lark Calendar에 미러링한다.
기존 미러링 이벤트(🔄 접두사)를 삭제 후 재생성하는 전략.

사용법:
    python3 scripts/gcal_sync.py              # 내일 1일치 동기화
    python3 scripts/gcal_sync.py --days 7     # 7일치 동기화
    python3 scripts/gcal_sync.py --days 3 --dry-run  # 미리보기
"""

import os
import sys
import json
import argparse
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 스크립트 디렉토리 추가 (sibling module import)
sys.path.insert(0, str(Path(__file__).parent))

from lark_calendar import (
    _get_token, get_primary_calendar_id,
    list_events_for_date, delete_event, get_next_workday
)

# Google Calendar API
from google.oauth2 import service_account
from googleapiclient.discovery import build

MIRROR_PREFIX = "🔄"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def _get_google_credentials():
    """Google Service Account 인증 정보 로드

    GOOGLE_SERVICE_ACCOUNT_KEY 환경변수에서:
    - 파일 경로면 from_service_account_file()
    - JSON 문자열이면 from_service_account_info()
    """
    key_value = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")
    if not key_value:
        print("❌ GOOGLE_SERVICE_ACCOUNT_KEY 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    # 파일 경로인지 JSON 문자열인지 판별
    key_value = key_value.strip()
    if key_value.startswith("{"):
        # JSON 문자열 (CI/CD 환경)
        info = json.loads(key_value)
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        # 파일 경로
        path = os.path.expanduser(key_value)
        if not os.path.exists(path):
            print(f"❌ Service Account 키 파일을 찾을 수 없습니다: {path}")
            sys.exit(1)
        creds = service_account.Credentials.from_service_account_file(path, scopes=SCOPES)

    return creds


def _build_google_service(credentials):
    """Google Calendar API 서비스 객체 생성"""
    return build("calendar", "v3", credentials=credentials)


def fetch_google_events(service, calendar_id: str, target_date: datetime) -> list[dict]:
    """특정 날짜의 Google Calendar 이벤트 조회

    Returns:
        list of dicts: [{summary, start_dt, end_dt, html_link, is_all_day}, ...]
    """
    # 날짜 범위 (KST 기준 하루)
    day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = target_date.replace(hour=23, minute=59, second=59, microsecond=0)

    time_min = day_start.isoformat() + "+09:00"
    time_max = day_end.isoformat() + "+09:00"

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy="startTime",
        timeZone="Asia/Seoul",
    ).execute()

    items = events_result.get("items", [])
    parsed = []

    for item in items:
        summary = item.get("summary", "(제목 없음)")
        html_link = item.get("htmlLink", "")
        start = item.get("start", {})
        end = item.get("end", {})

        # 종일 이벤트 판별
        if "dateTime" not in start:
            parsed.append({
                "summary": summary,
                "start_dt": None,
                "end_dt": None,
                "html_link": html_link,
                "is_all_day": True,
            })
            continue

        start_dt = datetime.fromisoformat(start["dateTime"])
        end_dt = datetime.fromisoformat(end["dateTime"])

        parsed.append({
            "summary": summary,
            "start_dt": start_dt,
            "end_dt": end_dt,
            "html_link": html_link,
            "is_all_day": False,
        })

    return parsed


def find_mirrored_events(events: list) -> list:
    """Lark 이벤트 목록에서 미러링된 이벤트(🔄 접두사) 필터링"""
    mirrored = []
    for event in events:
        summary = event.get("summary", "")
        if MIRROR_PREFIX in summary:
            mirrored.append(event)
    return mirrored


def delete_mirrored_events(events: list) -> int:
    """미러링된 이벤트 일괄 삭제"""
    deleted = 0
    for event in events:
        event_id = event.get("event_id")
        summary = event.get("summary", "")
        if event_id and delete_event(event_id):
            print(f"  🗑️ 삭제: {summary}")
            deleted += 1
            time.sleep(0.1)  # Rate limit 방지
    return deleted


def create_mirrored_event(calendar_id: str, token: str,
                          summary: str, description: str,
                          start_dt: datetime, end_dt: datetime) -> bool:
    """Google 이벤트를 Lark 캘린더에 미러링 생성"""
    url = f"https://open.larksuite.com/open-apis/calendar/v4/calendars/{calendar_id}/events"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "summary": f"{MIRROR_PREFIX} {summary}",
        "description": description,
        "start_time": {
            "timestamp": str(int(start_dt.timestamp()))
        },
        "end_time": {
            "timestamp": str(int(end_dt.timestamp()))
        },
        "visibility": "default",
        "free_busy_status": "busy"
    }

    response = requests.post(url, headers=headers, json=payload)
    data = response.json()

    if data.get("code") != 0:
        print(f"  ❌ 이벤트 생성 실패: {summary} - {data.get('msg')}")
        return False

    print(f"  ✅ 생성: {MIRROR_PREFIX} {summary} ({start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')})")
    return True


def sync_date(service, google_calendar_id: str, target_date: datetime,
              dry_run: bool = False) -> dict:
    """특정 날짜의 Google → Lark 동기화 실행"""
    weekday_names = ['월', '화', '수', '목', '금', '토', '일']
    day_name = weekday_names[target_date.weekday()]
    date_str = target_date.strftime('%m/%d')

    result = {
        "date": target_date.strftime("%Y-%m-%d"),
        "google_events": 0,
        "deleted": 0,
        "created": 0,
        "skipped_all_day": 0,
        "errors": [],
    }

    prefix = "🔍 [DRY RUN]" if dry_run else "📅"
    print(f"\n{prefix} {date_str}({day_name}) 동기화")

    # 1. Google Calendar 이벤트 조회
    google_events = fetch_google_events(service, google_calendar_id, target_date)
    result["google_events"] = len(google_events)

    timed_events = [e for e in google_events if not e["is_all_day"]]
    all_day_events = [e for e in google_events if e["is_all_day"]]
    result["skipped_all_day"] = len(all_day_events)

    print(f"  📥 Google 이벤트 {len(google_events)}개 (시간 지정: {len(timed_events)}, 종일: {len(all_day_events)})")

    for e in timed_events:
        print(f"    - {e['start_dt'].strftime('%H:%M')}-{e['end_dt'].strftime('%H:%M')} {e['summary']}")
    for e in all_day_events:
        print(f"    - [종일] {e['summary']} (스킵)")

    # 2. Lark Calendar에서 기존 미러링 이벤트 삭제
    lark_events = list_events_for_date(target_date)
    mirrored = find_mirrored_events(lark_events)

    if mirrored:
        print(f"  🗑️ 기존 미러링 이벤트 {len(mirrored)}개 삭제" + (" 예정" if dry_run else ""))
        if not dry_run:
            result["deleted"] = delete_mirrored_events(mirrored)
    else:
        print("  🗑️ 기존 미러링 이벤트 없음")

    # 3. Google 이벤트 → Lark 이벤트 생성
    if not timed_events:
        print("  ➡️ 생성할 이벤트 없음")
        return result

    lark_calendar_id = get_primary_calendar_id()
    token = _get_token()

    if not lark_calendar_id or not token:
        result["errors"].append("Lark 인증 실패")
        return result

    print(f"  ➕ {len(timed_events)}개 이벤트 생성" + (" 예정" if dry_run else ""))

    for event in timed_events:
        if dry_run:
            continue

        description = f"Google Calendar 미러링\n원본: {event['html_link']}"
        try:
            success = create_mirrored_event(
                lark_calendar_id, token,
                event["summary"], description,
                event["start_dt"], event["end_dt"]
            )
            if success:
                result["created"] += 1
            else:
                result["errors"].append(f"생성 실패: {event['summary']}")
            time.sleep(0.1)  # Rate limit 방지
        except Exception as e:
            print(f"  ⚠️ 이벤트 생성 실패: {event['summary']} - {e}")
            result["errors"].append(str(e))

    return result


def main():
    """메인 함수 - CLI 파싱 및 동기화 실행"""
    parser = argparse.ArgumentParser(description="Google Calendar → Lark Calendar 동기화")
    parser.add_argument("--days", type=int, default=1, help="동기화할 일수 (기본: 1 = 내일만)")
    parser.add_argument("--dry-run", action="store_true", help="실제 생성/삭제 없이 미리보기만")
    args = parser.parse_args()

    google_calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
    if not google_calendar_id:
        print("❌ GOOGLE_CALENDAR_ID 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    # Google Calendar 초기화
    print("🔑 Google Calendar 인증 중...")
    creds = _get_google_credentials()
    service = _build_google_service(creds)

    # 대상 날짜 범위 계산 (내일부터)
    start_date = get_next_workday()
    dates = []
    current = start_date
    for _ in range(args.days):
        dates.append(current)
        current = get_next_workday(current)

    mode = "[DRY RUN] " if args.dry_run else ""
    print(f"\n{'=' * 50}")
    print(f"🔄 {mode}Google → Lark 캘린더 동기화")
    print(f"📆 범위: {dates[0].strftime('%m/%d')} ~ {dates[-1].strftime('%m/%d')} ({len(dates)}일)")
    print(f"📧 Google Calendar: {google_calendar_id}")
    print(f"{'=' * 50}")

    # 날짜별 동기화
    results = []
    for target_date in dates:
        try:
            result = sync_date(service, google_calendar_id, target_date, args.dry_run)
            results.append(result)
        except Exception as e:
            print(f"\n❌ {target_date.strftime('%m/%d')} 동기화 실패: {e}")
            results.append({
                "date": target_date.strftime("%Y-%m-%d"),
                "google_events": 0, "deleted": 0, "created": 0,
                "skipped_all_day": 0, "errors": [str(e)]
            })

    # 요약 출력
    total_google = sum(r["google_events"] for r in results)
    total_deleted = sum(r["deleted"] for r in results)
    total_created = sum(r["created"] for r in results)
    total_skipped = sum(r["skipped_all_day"] for r in results)
    total_errors = sum(len(r["errors"]) for r in results)

    print(f"\n{'=' * 50}")
    print(f"📊 동기화 완료 요약")
    print(f"  Google 이벤트: {total_google}개")
    print(f"  삭제 (기존 미러링): {total_deleted}개")
    print(f"  생성: {total_created}개")
    print(f"  스킵 (종일): {total_skipped}개")
    if total_errors:
        print(f"  ⚠️ 에러: {total_errors}건")
    print(f"{'=' * 50}")

    if total_google == 0 and args.days > 0:
        print("\n💡 이벤트가 0개입니다. Google Calendar가 Service Account에 공유되어 있는지 확인하세요.")


if __name__ == "__main__":
    main()
