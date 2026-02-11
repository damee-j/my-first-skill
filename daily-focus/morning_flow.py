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
from lark_calendar import list_today_events, find_free_slots, create_focus_block, is_weekday, get_remaining_weekdays

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


def format_focus_summary(task, scope_result, free_slots, created_blocks, needed_hours, remaining_hours):
    """Focus 요약 메시지 포맷팅"""
    # 조회 범위 정보
    start_date, end_date = get_remaining_weekdays()
    weekday_names = ['월', '화', '수', '목', '금']
    remaining_days = [weekday_names[i] for i in range(datetime.now().weekday(), 5)]
    remaining_str = ', '.join(remaining_days)

    summary = f"""🎯 **이번 주 Focus**
"{task}"

📏 **스콥 분석**
- 작업 복잡도: {scope_result['complexity']}
- 예상 필요 시간: {scope_result['estimated_hours']}시간
- 분석 근거: {scope_result['reasoning']}
"""

    # 조언이 있으면 추가
    if 'advice' in scope_result and scope_result['advice']:
        summary += f"\n💡 **작업 조언**\n{scope_result['advice']}\n"

    summary += f"""
📅 **이번 주 일정 ({remaining_str})**
"""

    # 일정 목록 (오늘 것만 간략히)
    events = list_today_events()
    today_events = [e for e in events if datetime.fromtimestamp(int(e.get("start_time", {}).get("timestamp", 0))).date() == datetime.now().date()]

    if today_events:
        summary += f"- 오늘: {len(today_events)}개 일정\n"
        for event in today_events[:3]:  # 최대 3개만
            start = event.get("start_time", {})
            if "timestamp" in start:
                start_dt = datetime.fromtimestamp(int(start["timestamp"]))
                summary += f"  - {start_dt.strftime('%H:%M')} {event.get('summary', '제목 없음')}\n"

    if created_blocks:
        total_minutes = sum(block['duration'] for block in created_blocks)
        secured_hours = total_minutes / 60

        # 부분 성공 vs 완전 성공
        if remaining_hours > 0:
            summary += f"\n⚠️ **Focus Block 부분 생성**\n"
            summary += f"필요: {needed_hours}시간 → 확보: {secured_hours:.1f}시간\n"
            summary += f"\n📋 생성된 블록:\n"
        else:
            summary += f"\n🔒 **Focus Block 생성 완료!**\n"

        # 날짜별로 그룹화
        for block in created_blocks:
            start_dt = datetime.fromisoformat(block['start'])
            end_dt = start_dt + timedelta(minutes=block['duration'])
            date_str = start_dt.strftime('%m/%d(%a)')
            time_str = f"{start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')}"
            summary += f"- {date_str} {time_str} ({block['duration']/60:.1f}시간)\n"

        if remaining_hours > 0:
            summary += f"\n💡 **{remaining_hours:.1f}시간 부족**\n"
            summary += "일정을 조정하거나, 작업을 나눠서 진행하는 건 어떨까요?\n"
        else:
            summary += "\n이 시간엔 다른 미팅이 끼어들 수 없어요! 집중해봐요 💪"
    else:
        summary += "\n⚠️ **Focus Block을 생성하지 못했습니다**\n"
        summary += f"이번 주 남은 평일({remaining_str})에 빈 시간이 없어요. 일정 조정이 필요할 것 같아요.\n"

    return summary


def check_lark_token():
    """Lark 토큰 유효성 체크 (토큰 매니저로 자동 갱신)"""
    try:
        from lark_token_manager import get_valid_token

        token = get_valid_token()

        if token:
            print("✅ Lark 토큰 유효 (자동 갱신 완료)")
            return True
        else:
            print("❌ 유효한 Lark 토큰이 없습니다")
            send_dm("""⚠️ **Lark 캘린더 연동 필요**

daily-focus 스킬을 사용하려면 Lark 로그인이 필요해요.

터미널에서 다음 명령어를 실행해주세요:
```
python3 ~/dev/my-first-skill/daily-focus/scripts/lark_oauth.py
```

로그인 후 다시 시도해주세요!""")
            return False
    except Exception as e:
        print(f"⚠️ 토큰 체크 중 오류: {e}")
        # fallback: 환경변수 직접 확인
        token = os.getenv("LARK_USER_TOKEN")
        if token:
            print("⚠️ 토큰 매니저 오류, 환경변수 토큰으로 진행")
            return True
        return False


def main():
    """메인 함수"""
    print("=" * 60)
    print("🌅 아침 워크플로우 시작")
    print("=" * 60)

    # 0. 평일 체크 (월~금만 실행)
    if not is_weekday():
        weekday_names = ['월', '화', '수', '목', '금', '토', '일']
        today_name = weekday_names[datetime.now().weekday()]
        print(f"\n💤 오늘은 {today_name}요일입니다.")
        print("daily-focus는 평일(월~금)에만 실행됩니다.")
        send_dm(f"💤 오늘은 {today_name}요일! 푹 쉬세요~ 평일에 다시 만나요!")
        return

    # 남은 평일 정보
    start_date, end_date = get_remaining_weekdays()
    days_count = (end_date - start_date).days + 1
    print(f"\n📅 조회 대상: 이번 주 남은 평일 {days_count}일 ({start_date.strftime('%m/%d')} ~ {end_date.strftime('%m/%d')})")

    # 1. Lark 토큰 체크
    print("\n🔐 Lark 토큰 체크 중...")
    if not check_lark_token():
        print("❌ Lark 토큰이 유효하지 않습니다. 종료합니다.")
        return

    # 2. Slack DM으로 인사
    weekday_names = ['월', '화', '수', '목', '금']
    remaining_days = [weekday_names[i] for i in range(datetime.now().weekday(), 5)]
    remaining_str = ', '.join(remaining_days)

    greeting = f"""🌅 좋은 아침이에요!

이번 주 남은 평일({remaining_str})에 딱 한 가지, 가장 집중하고 싶은 일은 뭐예요?

**형식**: 작업 내용 | 필요한 시간(선택)
**예시**:
• "PRD 초안 작성 | 4시간"
• "클라이언트 미팅 준비"
• "코드 리뷰 | 1.5"

시간을 입력하지 않으면 자동으로 추정해드려요! 💡
이번 주 남은 {days_count}일 동안의 빈 시간을 확인해서 Focus Block을 만들어드릴게요."""

    send_dm(greeting)
    print("✅ 인사 메시지 발송 완료")

    # 2. 사용자 응답 대기
    user_response = wait_for_user_response(timeout_minutes=5)

    if not user_response:
        # 무응답 시 재시도 안내
        send_dm("응답이 없어서 아직 집중할 일을 정하지 못했어요. 준비되면 다시 시작해주세요!")
        return

    # 3. 사용자 입력 파싱 (작업 | 시간)
    task_text = user_response
    user_specified_hours = None

    if '|' in user_response:
        parts = user_response.split('|')
        task_text = parts[0].strip()
        time_part = parts[1].strip()

        # 시간 파싱
        import re
        time_match = re.search(r'(\d+\.?\d*)', time_part)
        if time_match:
            user_specified_hours = float(time_match.group(1))
            print(f"✅ 사용자 지정 시간: {user_specified_hours}시간")

    # 4. 스콥 분석
    print(f"\n📏 스콥 분석 중... (작업: {task_text})")

    if user_specified_hours:
        # 사용자가 시간을 지정한 경우
        scope_result = {
            "complexity": "사용자 지정",
            "estimated_hours": user_specified_hours,
            "reasoning": "사용자가 직접 입력한 시간",
            "breakdown": [f"{task_text}: {user_specified_hours}시간"],
            "advice": "스스로 정한 시간만큼 집중해서 진행하세요. 중간에 점검하며 진행 상황을 확인하세요."
        }
        print(f"✅ 사용자 지정 시간 사용: {user_specified_hours}시간")
    else:
        # 키워드 기반 휴리스틱 추정 (AI API quota 부족 시)
        scope_result = analyze_scope(task_text)
        print(f"✅ 자동 추정 완료: {scope_result['estimated_hours']}시간 ({scope_result['reasoning']})")

    needed_hours = scope_result["estimated_hours"]
    needed_minutes = int(needed_hours * 60)

    # 사용자에게 추정 결과 알림
    analysis_message = f"""📊 **작업 스콥 분석**

**작업**: {task_text}
**예상 시간**: {needed_hours}시간
**추정 방식**: {scope_result['reasoning']}
"""

    # 조언이 있으면 추가
    if 'advice' in scope_result and scope_result['advice']:
        analysis_message += f"\n💡 **작업 조언**\n{scope_result['advice']}\n"

    analysis_message += "\n캘린더에서 빈 시간을 찾아볼게요... 🔍"

    send_dm(analysis_message)

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

        # Focus Block 생성 (task_text 사용)
        start_iso = free_start.isoformat()
        success = create_focus_block(task_text, start_iso, block_minutes)

        if success:
            created_blocks.append({
                "start": start_iso,
                "duration": block_minutes
            })
            remaining_minutes -= block_minutes

    # 6. Slack으로 요약 전송
    print("\n📤 요약 메시지 발송...")

    # 부분 성공 여부 확인
    is_partial_success = remaining_minutes > 0 and created_blocks

    summary = format_focus_summary(
        task_text,
        scope_result,
        free_slots,
        created_blocks,
        needed_hours,
        remaining_minutes / 60 if remaining_minutes > 0 else 0
    )
    send_dm(summary)

    # 7. 로그 저장 (저녁 회고 시 사용)
    log_dir = Path.home() / ".daily-focus"
    log_dir.mkdir(exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"{today}.json"

    import json
    log_data = {
        "date": today,
        "focus_task": task_text,  # 파싱된 작업명 저장
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
