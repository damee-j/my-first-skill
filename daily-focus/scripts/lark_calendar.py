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

from lark_token_manager import get_valid_token


def _get_token():
    """유효한 Lark 토큰 반환 (자동 갱신 포함)"""
    token = get_valid_token()
    if token:
        return token

    # 토큰 매니저 실패 시 환경변수 fallback
    token = os.getenv("LARK_USER_TOKEN")
    if not token:
        print("❌ 유효한 Lark 토큰이 없습니다. python3 scripts/lark_oauth.py를 실행해주세요.")
    return token


def is_weekday():
    """평일(월~금) 체크"""
    return datetime.now().weekday() < 5  # 0=월요일, 4=금요일


def get_remaining_weekdays():
    """이번 주 남은 평일 범위 계산 (오늘 ~ 금요일)"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    weekday = today.weekday()  # 0=월, 1=화, ..., 6=일

    # 주말이면 다음 주 월요일부터
    if weekday >= 5:  # 토요일(5) or 일요일(6)
        days_until_monday = 7 - weekday
        start_date = today + timedelta(days=days_until_monday)
        end_date = start_date + timedelta(days=4)  # 월~금
    else:
        # 평일이면 오늘부터 이번 주 금요일까지
        start_date = today
        days_until_friday = 4 - weekday  # 금요일까지 남은 일수
        end_date = today + timedelta(days=days_until_friday)

    return start_date, end_date


def get_primary_calendar_id():
    """Primary 캘린더 ID 조회 (type='primary'만 사용, Google 캘린더 제외)"""
    token = _get_token()
    if not token:
        return None

    url = "https://open.larksuite.com/open-apis/calendar/v4/calendars"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    if data.get("code") != 0:
        print(f"❌ 캘린더 조회 실패: {data.get('msg')}")
        return None

    calendars = data.get("data", {}).get("calendar_list", [])

    # type='primary'인 캘린더만 사용 (Google 캘린더는 지원 안 됨)
    primary = next((cal for cal in calendars if cal.get("type") == "primary"), None)

    if not primary:
        print("❌ Primary 캘린더를 찾을 수 없습니다.")
        return None

    return primary["calendar_id"]


def list_today_events():
    """오늘 일정 조회 (레거시 호환용)"""
    return list_remaining_weekday_events()


def list_remaining_weekday_events():
    """이번 주 남은 평일 일정 조회 (오늘 ~ 금요일)"""
    calendar_id = get_primary_calendar_id()
    if not calendar_id:
        return []

    # 이번 주 남은 평일 범위 계산
    start_date, end_date = get_remaining_weekdays()

    # Unix timestamp (seconds)
    range_start = int(start_date.timestamp())
    range_end = int(end_date.replace(hour=23, minute=59, second=59).timestamp())

    token = _get_token()
    if not token:
        return []

    url = f"https://open.larksuite.com/open-apis/calendar/v4/calendars/{calendar_id}/events"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    params = {
        "start_time": range_start,
        "end_time": range_end
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if data.get("code") != 0:
        print(f"❌ 일정 조회 실패: {data.get('msg')}")
        return []

    events = data.get("data", {}).get("items", [])

    # 디버그: 조회 범위 출력
    print(f"📅 일정 조회 범위: {start_date.strftime('%m/%d(%a)')} ~ {end_date.strftime('%m/%d(%a)')}")

    return events


def find_free_slots(duration_minutes: int, min_block_minutes: int = 30):
    """빈 시간 찾기 - 이번 주 남은 평일 대상 (월~금, 10:00-19:00, 점심 제외)

    Args:
        duration_minutes: 필요한 총 시간 (참고용)
        min_block_minutes: 최소 블록 크기 (기본 30분)

    Returns:
        list: (start_dt, end_dt, gap_minutes) 튜플의 리스트
    """
    # 남은 평일 범위 계산
    start_date, end_date = get_remaining_weekdays()

    # 평일 일정 조회
    events = list_remaining_weekday_events()

    # 날짜별로 빈 시간 찾기
    all_free_slots = []
    current_date = start_date

    while current_date <= end_date:
        # 주말 건너뛰기
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue

        # 이 날짜의 근무시간 정의 (10:00 ~ 19:00)
        work_start = current_date.replace(hour=10, minute=0, second=0, microsecond=0)
        work_end = current_date.replace(hour=19, minute=0, second=0, microsecond=0)

        # 이 날짜의 바쁜 시간 수집
        busy_slots = []

        # 점심시간 추가 (11:00 ~ 12:00)
        lunch_start = current_date.replace(hour=11, minute=0, second=0, microsecond=0)
        lunch_end = current_date.replace(hour=12, minute=0, second=0, microsecond=0)
        busy_slots.append((lunch_start, lunch_end))

        # 이 날짜의 일정 추가
        for event in events:
            start = event.get("start_time", {})
            end = event.get("end_time", {})

            if "timestamp" in start and "timestamp" in end:
                start_dt = datetime.fromtimestamp(int(start["timestamp"]))
                end_dt = datetime.fromtimestamp(int(end["timestamp"]))

                # 같은 날짜의 일정만 포함
                if start_dt.date() == current_date.date():
                    busy_slots.append((start_dt, end_dt))

        busy_slots.sort()

        # 빈 시간 찾기
        current_time = work_start

        for busy_start, busy_end in busy_slots:
            if busy_start > current_time:
                gap_minutes = int((busy_start - current_time).total_seconds() / 60)
                if gap_minutes >= min_block_minutes:
                    all_free_slots.append((current_time, busy_start, gap_minutes))

            current_time = max(current_time, busy_end)

        # 마지막 빈 시간 확인
        if current_time < work_end:
            gap_minutes = int((work_end - current_time).total_seconds() / 60)
            if gap_minutes >= min_block_minutes:
                all_free_slots.append((current_time, work_end, gap_minutes))

        current_date += timedelta(days=1)

    return all_free_slots


def get_next_workday(from_date=None):
    """다음 근무일 계산 (금→월, 토→월, 일→월)"""
    if from_date is None:
        from_date = datetime.now()
    target = from_date + timedelta(days=1)
    target = target.replace(hour=0, minute=0, second=0, microsecond=0)

    # 주말이면 다음 월요일로
    while target.weekday() >= 5:
        target += timedelta(days=1)

    return target


def list_events_for_date(target_date):
    """특정 날짜의 일정 조회 (instance_view로 반복 일정의 실제 발생 시각 반환)"""
    calendar_id = get_primary_calendar_id()
    if not calendar_id:
        return []

    range_start = int(target_date.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    range_end = int(target_date.replace(hour=23, minute=59, second=59, microsecond=0).timestamp())

    token = _get_token()
    if not token:
        return []

    url = f"https://open.larksuite.com/open-apis/calendar/v4/calendars/{calendar_id}/events/instance_view"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    params = {
        "start_time": str(range_start),
        "end_time": str(range_end)
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if data.get("code") != 0:
        print(f"❌ 일정 조회 실패: {data.get('msg')}")
        return []

    events = data.get("data", {}).get("items", [])
    weekday_names = ['월', '화', '수', '목', '금', '토', '일']
    day_name = weekday_names[target_date.weekday()]
    print(f"📅 {target_date.strftime('%m/%d')}({day_name}) 일정 조회: {len(events)}개")

    return events


def find_free_slots_for_date(target_date, duration_minutes: int, min_block_minutes: int = 30):
    """특정 날짜의 빈 시간 찾기 (10:00-19:00, 점심 제외, 9:30-11:00 Focus 윈도우 내 일정 무시)

    Args:
        target_date: 대상 날짜 (datetime)
        duration_minutes: 필요한 총 시간 (참고용)
        min_block_minutes: 최소 블록 크기 (기본 30분)

    Returns:
        list: (start_dt, end_dt, gap_minutes) 튜플의 리스트
    """
    events = list_events_for_date(target_date)

    # 근무시간 정의
    work_start = target_date.replace(hour=10, minute=0, second=0, microsecond=0)
    work_end = target_date.replace(hour=19, minute=0, second=0, microsecond=0)

    # 9:30-11:00 Focus 전용 윈도우 (이 안의 일정은 무시)
    focus_window_start = target_date.replace(hour=9, minute=30, second=0, microsecond=0)
    focus_window_end = target_date.replace(hour=11, minute=0, second=0, microsecond=0)

    # 바쁜 시간 수집
    busy_slots = []

    # 점심시간 (11:00-12:00)
    lunch_start = target_date.replace(hour=11, minute=0, second=0, microsecond=0)
    lunch_end = target_date.replace(hour=12, minute=0, second=0, microsecond=0)
    busy_slots.append((lunch_start, lunch_end))

    for event in events:
        start = event.get("start_time", {})
        end = event.get("end_time", {})

        if "timestamp" in start and "timestamp" in end:
            start_dt = datetime.fromtimestamp(int(start["timestamp"]))
            end_dt = datetime.fromtimestamp(int(end["timestamp"]))

            if start_dt.date() == target_date.date():
                # 9:30-11:00 윈도우 안에 완전히 포함된 일정은 무시
                if start_dt >= focus_window_start and end_dt <= focus_window_end:
                    continue

                # 종일 블록 무시 (8시간 이상: 재택, WFH 등 배경 일정)
                duration_hrs = (end_dt - start_dt).total_seconds() / 3600
                if duration_hrs >= 8:
                    continue

                # free_busy_status가 "free"인 일정 무시
                if event.get("free_busy_status") == "free":
                    continue

                busy_slots.append((start_dt, end_dt))

    busy_slots.sort()

    # 빈 시간 찾기
    free_slots = []
    current_time = work_start

    for busy_start, busy_end in busy_slots:
        if busy_start > current_time:
            gap_minutes = int((busy_start - current_time).total_seconds() / 60)
            if gap_minutes >= min_block_minutes:
                free_slots.append((current_time, busy_start, gap_minutes))
        current_time = max(current_time, busy_end)

    # 마지막 빈 시간
    if current_time < work_end:
        gap_minutes = int((work_end - current_time).total_seconds() / 60)
        if gap_minutes >= min_block_minutes:
            free_slots.append((current_time, work_end, gap_minutes))

    return free_slots


def create_focus_block(title: str, start_time: str, duration_minutes: int):
    """Focus Block 생성"""
    calendar_id = get_primary_calendar_id()
    if not calendar_id:
        return False

    token = _get_token()
    if not token:
        return False

    # 시작/종료 시간 계산
    start_dt = datetime.fromisoformat(start_time)
    end_dt = start_dt + timedelta(minutes=duration_minutes)

    url = f"https://open.larksuite.com/open-apis/calendar/v4/calendars/{calendar_id}/events"
    headers = {
        "Authorization": f"Bearer {token}",
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


def delete_event(event_id: str):
    """이벤트 삭제"""
    calendar_id = get_primary_calendar_id()
    if not calendar_id:
        return False

    token = _get_token()
    if not token:
        return False

    url = f"https://open.larksuite.com/open-apis/calendar/v4/calendars/{calendar_id}/events/{event_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.delete(url, headers=headers)
    data = response.json()

    if data.get("code") != 0:
        print(f"❌ 이벤트 삭제 실패: {data.get('msg')}")
        return False

    print(f"✅ 이벤트 삭제 성공: {event_id}")
    return True


def delete_focus_blocks_today(keyword: str = "🔒"):
    """오늘 생성된 Focus Block 삭제"""
    events = list_today_events()
    deleted_count = 0

    for event in events:
        summary = event.get("summary", "")
        if keyword in summary:
            event_id = event.get("event_id")
            if event_id and delete_event(event_id):
                deleted_count += 1
                print(f"  삭제: {summary}")

    return deleted_count


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
