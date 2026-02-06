#!/usr/bin/env python3
"""
Lark 캘린더 관리 스크립트

사용법:
    python3 lark_calendar.py --list-events  # 오늘 일정 조회
    python3 lark_calendar.py --find-gaps --duration 180  # 빈 시간 찾기 (분 단위)
    python3 lark_calendar.py --create-block --title "PRD 작성" --start "2026-02-06T10:00:00" --duration 180
"""

import os
import sys
import argparse
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# Token Manager 사용
try:
    from lark_token_manager import get_valid_token
    LARK_USER_TOKEN = get_valid_token()
    if not LARK_USER_TOKEN:
        print("❌ 유효한 Lark 토큰을 가져올 수 없습니다.")
        print("python3 scripts/lark_oauth.py를 실행하여 로그인해주세요.")
        sys.exit(1)
except ImportError:
    # Fallback: 환경변수에서 직접 읽기
    LARK_USER_TOKEN = os.getenv("LARK_USER_TOKEN")
    if not LARK_USER_TOKEN:
        print("❌ LARK_USER_TOKEN이 설정되지 않았습니다.")
        print("python3 scripts/lark_oauth.py를 실행하여 토큰을 발급받아주세요.")
        sys.exit(1)


def get_primary_calendar_id():
    """Primary 캘린더 ID 조회"""
    url = "https://open.larksuite.com/open-apis/calendar/v4/calendars"
    headers = {
        "Authorization": f"Bearer {LARK_USER_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    if data.get("code") != 0:
        print(f"❌ 캘린더 조회 실패: {data.get('msg')}")
        return None

    calendars = data.get("data", {}).get("calendar_list", [])
    primary = next((cal for cal in calendars if cal.get("role") == "owner"), None)

    if not primary:
        print("❌ Primary 캘린더를 찾을 수 없습니다.")
        return None

    return primary["calendar_id"]


def list_today_events():
    """오늘 일정 조회"""
    calendar_id = get_primary_calendar_id()
    if not calendar_id:
        return []

    # 오늘 00:00 ~ 23:59 (Unix timestamp, seconds)
    today_start = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    today_end = int(datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999).timestamp())

    url = f"https://open.larksuite.com/open-apis/calendar/v4/calendars/{calendar_id}/events"
    headers = {
        "Authorization": f"Bearer {LARK_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    params = {
        "start_time": today_start,
        "end_time": today_end
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if data.get("code") != 0:
        print(f"❌ 일정 조회 실패: {data.get('msg')}")
        return []

    events = data.get("data", {}).get("items", [])
    return events


def find_free_slots(duration_minutes: int):
    """빈 시간 찾기 (분 단위)"""
    events = list_today_events()

    # 일정을 시간 순으로 정렬
    busy_slots = []
    for event in events:
        start = event.get("start_time", {})
        end = event.get("end_time", {})

        # timestamp 변환 (seconds → datetime)
        if "timestamp" in start:
            start_dt = datetime.fromtimestamp(int(start["timestamp"]))
        else:
            continue

        if "timestamp" in end:
            end_dt = datetime.fromtimestamp(int(end["timestamp"]))
        else:
            continue

        busy_slots.append((start_dt, end_dt))

    busy_slots.sort()

    # 빈 시간 찾기 (근무 시간: 9:00 ~ 19:00)
    work_start = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    work_end = datetime.now().replace(hour=19, minute=0, second=0, microsecond=0)

    free_slots = []
    current_time = work_start

    for busy_start, busy_end in busy_slots:
        if busy_start > current_time:
            gap_minutes = int((busy_start - current_time).total_seconds() / 60)
            if gap_minutes >= duration_minutes:
                free_slots.append((current_time, busy_start, gap_minutes))

        current_time = max(current_time, busy_end)

    # 마지막 빈 시간 확인
    if current_time < work_end:
        gap_minutes = int((work_end - current_time).total_seconds() / 60)
        if gap_minutes >= duration_minutes:
            free_slots.append((current_time, work_end, gap_minutes))

    return free_slots


def create_focus_block(title: str, start_time: str, duration_minutes: int):
    """Focus Block 생성"""
    calendar_id = get_primary_calendar_id()
    if not calendar_id:
        return False

    # 시작/종료 시간 계산
    start_dt = datetime.fromisoformat(start_time)
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    url = f"https://open.larksuite.com/open-apis/calendar/v4/calendars/{calendar_id}/events"
    headers = {
        "Authorization": f"Bearer {LARK_USER_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "summary": f"🔒 {title}",
        "description": "Focus Block - 이 시간엔 미팅이 끼어들 수 없어요!",
        "start_time": {
            "timestamp": str(int(start_dt.timestamp()))
        },
        "end_time": {
            "timestamp": str(int(end_dt.timestamp()))
        },
        "visibility": "private",
        "free_busy_status": "busy"
    }

    response = requests.post(url, headers=headers, json=payload)
    data = response.json()

    if data.get("code") != 0:
        print(f"❌ Focus Block 생성 실패: {data.get('msg')}")
        return False

    print(f"✅ Focus Block 생성 성공: {title} ({start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')})")
    return True


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="Lark 캘린더 관리")
    parser.add_argument("--list-events", action="store_true", help="오늘 일정 조회")
    parser.add_argument("--find-gaps", action="store_true", help="빈 시간 찾기")
    parser.add_argument("--create-block", action="store_true", help="Focus Block 생성")
    parser.add_argument("--title", type=str, help="Focus Block 제목")
    parser.add_argument("--start", type=str, help="시작 시간 (ISO 8601)")
    parser.add_argument("--duration", type=int, help="필요 시간 (분)")

    args = parser.parse_args()

    if args.list_events:
        events = list_today_events()
        print(f"📅 오늘 일정 ({len(events)}개):")
        for event in events:
            summary = event.get("summary", "제목 없음")
            start = event.get("start_time", {})
            end = event.get("end_time", {})

            if "timestamp" in start and "timestamp" in end:
                start_dt = datetime.fromtimestamp(int(start["timestamp"]))
                end_dt = datetime.fromtimestamp(int(end["timestamp"]))
                print(f"  - {start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')} {summary}")

    elif args.find_gaps:
        if not args.duration:
            print("❌ --duration 옵션이 필요합니다.")
            sys.exit(1)

        free_slots = find_free_slots(args.duration)
        print(f"🔍 빈 시간 ({args.duration}분 이상):")
        for start, end, gap_minutes in free_slots:
            print(f"  - {start.strftime('%H:%M')}-{end.strftime('%H:%M')} ({gap_minutes}분)")

    elif args.create_block:
        if not args.title or not args.start or not args.duration:
            print("❌ --title, --start, --duration 옵션이 모두 필요합니다.")
            sys.exit(1)

        create_focus_block(args.title, args.start, args.duration)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
