#!/usr/bin/env python3
"""
아침 워크플로우 (10:00 실행)

흐름:
1. Lark 토큰 유효성 체크 (만료 시 Slack 알림)
2. Slack DM으로 인사 및 오늘 집중할 일 질문
3. 사용자 응답 대기 (5분 타임아웃)
4. 스콥 분석 및 필요시간 계산
5. Lark 캘린더 빈 시간 찾기
6. Focus Block 생성
7. Slack으로 요약 전송
"""

import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# 스크립트 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from slack_dm import send_dm, get_recent_messages
from scope_analyzer import analyze_scope
from lark_calendar import list_today_events, find_free_slots, create_focus_block

# .env 파일 로드 (lark_token_manager보다 먼저)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")


def wait_for_user_response(timeout_minutes=5):
    """사용자 응답 대기"""
    print(f"⏳ 사용자 응답 대기 중... (최대 {timeout_minutes}분)")

    start_time = time.time()
    timeout_seconds = timeout_minutes * 60

    # 현재 시간의 메시지 타임스탬프 저장
    initial_messages = get_recent_messages(limit=1)
    last_timestamp = float(initial_messages[0]["timestamp"]) if initial_messages else 0

    while True:
        # 타임아웃 체크
        if time.time() - start_time > timeout_seconds:
            print("⏰ 타임아웃: 응답이 없습니다.")
            return None

        # 30초마다 새 메시지 확인
        time.sleep(30)

        current_messages = get_recent_messages(limit=5)

        # 마지막 타임스탬프 이후의 새 메시지 찾기
        for msg in reversed(current_messages):  # 오래된 것부터 확인
            msg_timestamp = float(msg["timestamp"])
            if msg_timestamp > last_timestamp:
                # 봇 메시지가 아닌지 확인 (봇 메시지에는 bot_id가 있음)
                # 간단하게: 인사 메시지나 타임아웃 메시지가 아니면 사용자 응답으로 간주
                text = msg["text"]
                if "좋은 아침이에요" not in text and "응답이 없어서" not in text:
                    print(f"✅ 응답 받음: {text[:50]}...")
                    return text

        print(".", end="", flush=True)


def format_focus_summary(task, scope_result, free_slots, created_blocks):
    """Focus 요약 메시지 포맷팅"""
    summary = f"""🎯 **오늘의 Focus**
"{task}"

📏 **스콥 분석**
- 작업 복잡도: {scope_result['complexity']}
- 예상 필요 시간: {scope_result['estimated_hours']}시간
- 분석 근거: {scope_result['reasoning']}

📅 **오늘 일정 확인**
"""

    # 일정 목록 (간략하게)
    events = list_today_events()
    if events:
        summary += f"- 총 {len(events)}개 일정\n"
        for event in events[:3]:  # 최대 3개만
            start = event.get("start_time", {})
            if "timestamp" in start:
                start_dt = datetime.fromtimestamp(int(start["timestamp"]))
                summary += f"  - {start_dt.strftime('%H:%M')} {event.get('summary', '제목 없음')}\n"

    summary += f"\n🔒 **Focus Block 생성 완료!**\n"

    if created_blocks:
        total_minutes = sum(block['duration'] for block in created_blocks)
        for block in created_blocks:
            start_dt = datetime.fromisoformat(block['start'])
            end_dt = start_dt + timedelta(minutes=block['duration'])
            summary += f"- {start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')} ({block['duration']/60:.1f}시간)\n"

        summary += f"\n총 {total_minutes/60:.1f}시간 확보\n"
        summary += "\n이 시간엔 다른 미팅이 끼어들 수 없어요! 집중해봐요 💪"
    else:
        summary += "⚠️ Focus Block을 생성하지 못했습니다.\n"

    return summary


def check_lark_token():
    """Lark 토큰 유효성 체크"""
    try:
        from lark_token_manager import get_valid_token, load_tokens

        token = get_valid_token()

        if not token:
            # 토큰이 없거나 만료됨
            send_dm("""⚠️ **Lark 캘린더 연동 필요**

daily-focus 스킬을 사용하려면 Lark 로그인이 필요해요.

터미널에서 다음 명령어를 실행해주세요:
```
python3 ~/dev/my-first-skill/daily-focus/scripts/lark_oauth.py
```

로그인 후 다시 시도해주세요!""")
            return False

        # 토큰 만료 임박 확인 (24시간 이내)
        token_data = load_tokens()
        if token_data:
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            time_left = expires_at - datetime.now()

            if time_left < timedelta(hours=24):
                send_dm(f"""📅 **Lark 토큰 만료 임박**

토큰이 {time_left.total_seconds()/3600:.1f}시간 후에 만료됩니다.

곧 재로그인이 필요할 수 있어요!""")

        return True

    except ImportError:
        # Token manager가 없으면 기본 동작
        return True
    except Exception as e:
        print(f"⚠️ 토큰 체크 중 오류: {e}")
        return True  # 오류가 있어도 계속 진행


def main():
    """메인 함수"""
    print("=" * 60)
    print("🌅 아침 워크플로우 시작")
    print("=" * 60)

    # 0. Lark 토큰 체크
    print("\n🔐 Lark 토큰 체크 중...")
    if not check_lark_token():
        print("❌ Lark 토큰이 유효하지 않습니다. 종료합니다.")
        return

    # 1. Slack DM으로 인사
    greeting = """🌅 좋은 아침이에요!

오늘 딱 한 가지, 가장 집중하고 싶은 일은 뭐예요?"""

    send_dm(greeting)
    print("✅ 인사 메시지 발송 완료")

    # 2. 사용자 응답 대기
    user_response = wait_for_user_response(timeout_minutes=5)

    if not user_response:
        # 무응답 시 재시도 안내
        send_dm("응답이 없어서 아직 집중할 일을 정하지 못했어요. 준비되면 '/daily-focus'를 다시 실행해주세요!")
        return

    # 3. 스콥 분석
    print("\n📏 스콥 분석 중...")
    scope_result = analyze_scope(user_response)

    needed_hours = scope_result["estimated_hours"]
    needed_minutes = int(needed_hours * 60)

    print(f"✅ 스콥 분석 완료: {needed_hours}시간 필요")

    # 4. Lark 캘린더 빈 시간 찾기
    print("\n🔍 캘린더 빈 시간 찾기...")
    free_slots = find_free_slots(needed_minutes)

    if not free_slots:
        # 빈 시간 부족
        message = f"""😔 캘린더에 연속된 빈 시간이 부족해요.

**필요한 시간**: {needed_hours}시간
**오늘 집중할 일**: {user_response}

일정을 조정하거나 작업 범위를 줄여볼까요?"""
        send_dm(message)
        return

    print(f"✅ {len(free_slots)}개 빈 시간 발견")

    # 5. Focus Block 생성
    print("\n🔒 Focus Block 생성 중...")
    created_blocks = []
    remaining_minutes = needed_minutes

    for free_start, free_end, gap_minutes in free_slots:
        if remaining_minutes <= 0:
            break

        # 이 빈 시간에 할당할 시간 계산
        block_minutes = min(remaining_minutes, gap_minutes)

        # Focus Block 생성
        start_iso = free_start.isoformat()
        success = create_focus_block(user_response, start_iso, block_minutes)

        if success:
            created_blocks.append({
                "start": start_iso,
                "duration": block_minutes
            })
            remaining_minutes -= block_minutes

    # 6. Slack으로 요약 전송
    print("\n📤 요약 메시지 발송...")
    summary = format_focus_summary(user_response, scope_result, free_slots, created_blocks)
    send_dm(summary)

    # 7. 로그 저장 (저녁 회고 시 사용)
    log_dir = Path.home() / ".daily-focus"
    log_dir.mkdir(exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"{today}.json"

    import json
    log_data = {
        "date": today,
        "focus_task": user_response,
        "scope_analysis": scope_result,
        "focus_blocks": created_blocks
    }

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    print(f"💾 로그 저장 완료: {log_file}")

    print("\n" + "=" * 60)
    print("✅ 아침 워크플로우 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
