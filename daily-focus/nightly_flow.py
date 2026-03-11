#!/usr/bin/env python3
"""
나이틀리 워크플로우 (22:00 KST 실행)

통합 플로우:
- Part A: 오늘의 회고 (4가지 질문 → 기록 저장)
- Part B: 내일의 Focus Block 생성
"""

import os
import sys
import re
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

# 스크립트 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from lark_im import send_message
from lark_event_listener import start_listener, wait_for_message, clear_queue
from scope_analyzer import analyze_scope
from lark_calendar import (
    find_free_slots_for_date, create_focus_block,
    list_events_for_date, get_next_workday
)
# .env 파일 로드
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")


def check_lark_token():
    """Lark 토큰 유효성 체크 (캘린더용)"""
    try:
        from lark_token_manager import get_valid_token

        token = get_valid_token()
        if token:
            print("✅ Lark 토큰 유효 (자동 갱신 완료)")
            return True
        else:
            print("❌ 유효한 Lark 토큰이 없습니다")
            send_message("""⚠️ Lark 캘린더 연동 필요

daily-focus 스킬을 사용하려면 Lark 로그인이 필요해요.

터미널에서 다음 명령어를 실행해주세요:
python3 ~/dev/my-first-skill/daily-focus/scripts/lark_oauth.py

로그인 후 다시 시도해주세요!""")
            return False
    except Exception as e:
        print(f"⚠️ 토큰 체크 중 오류: {e}")
        token = os.getenv("LARK_USER_TOKEN")
        if token:
            print("⚠️ 토큰 매니저 오류, 환경변수 토큰으로 진행")
            return True
        return False


def run_reflection():
    """Part A: 오늘의 회고"""
    print("\n" + "=" * 60)
    print("📝 Part A: 오늘의 회고")
    print("=" * 60)

    reflection_message = """🌙 하루 고생하셨어요! 오늘의 회고 시간이에요.

아래 4가지에 대해 자유롭게 답해주세요:

1. 오늘 관찰한 가장 중요한 일
2. 오늘 배운 일
3. 오늘 실행한 일
4. 그냥 떠오른 중요한 생각

편하게 한 번에 적어주세요!"""

    clear_queue()
    send_message(reflection_message)
    print("✅ 회고 질문 발송 완료")

    # 사용자 응답 대기 (그룹 채팅 폴링)
    user_response = wait_for_message(timeout_minutes=15)

    if not user_response:
        send_message("응답이 없어서 회고를 건너뛸게요. 내일 Focus 질문으로 넘어갑니다!")
        return None

    # 회고 기록 확인
    send_message("💾 회고 기록 완료! 오늘 하루도 고생 많으셨어요.")

    return {
        "user_response": user_response,
        "timestamp": datetime.now().isoformat()
    }


def run_tomorrow_focus(target_date):
    """Part B: 내일의 Focus"""
    print("\n" + "=" * 60)
    print("🎯 Part B: 내일의 Focus")
    print("=" * 60)

    weekday_names = ['월', '화', '수', '목', '금', '토', '일']
    day_name = weekday_names[target_date.weekday()]

    focus_message = f"""내일({target_date.strftime('%m/%d')} {day_name}요일) 딱 한 가지, 가장 집중하고 싶은 일은 뭐예요?

형식: 작업 내용 | 필요한 시간(선택)
예시: "PRD 초안 작성 | 4시간"

시간을 입력하지 않으면 자동으로 추정해드려요!"""

    clear_queue()
    send_message(focus_message)
    print("✅ Focus 질문 발송 완료")

    # 사용자 응답 대기 (그룹 채팅 폴링)
    user_response = wait_for_message(timeout_minutes=15)

    if not user_response:
        send_message("응답이 없어서 Focus Block 생성을 건너뛸게요. 편히 쉬세요!")
        return None

    # 사용자 입력 파싱 (작업 | 시간)
    task_text = user_response
    user_specified_hours = None

    if '|' in user_response:
        parts = user_response.split('|')
        task_text = parts[0].strip()
        time_part = parts[1].strip()

        time_match = re.search(r'(\d+\.?\d*)', time_part)
        if time_match:
            user_specified_hours = float(time_match.group(1))
            print(f"✅ 사용자 지정 시간: {user_specified_hours}시간")

    # 스콥 분석
    print(f"\n📏 스콥 분석 중... (작업: {task_text})")

    if user_specified_hours:
        scope_result = {
            "complexity": "사용자 지정",
            "estimated_hours": user_specified_hours,
            "reasoning": "사용자가 직접 입력한 시간",
            "breakdown": [f"{task_text}: {user_specified_hours}시간"],
            "advice": "스스로 정한 시간만큼 집중해서 진행하세요."
        }
    else:
        scope_result = analyze_scope(task_text)
        print(f"✅ 자동 추정 완료: {scope_result['estimated_hours']}시간 ({scope_result['reasoning']})")

    needed_hours = scope_result["estimated_hours"]
    needed_minutes = int(needed_hours * 60)

    # 스콥 분석 결과 알림
    analysis_message = f"""📊 작업 스콥 분석

작업: {task_text}
예상 시간: {needed_hours}시간
추정 방식: {scope_result['reasoning']}"""

    if scope_result.get('advice'):
        analysis_message += f"\n\n💡 작업 조언\n{scope_result['advice']}"

    analysis_message += f"\n\n내일({day_name}요일) 캘린더에서 빈 시간을 찾아볼게요... 🔍"

    send_message(analysis_message)

    # 내일 캘린더 빈 시간 찾기
    print("\n🔍 내일 캘린더 빈 시간 찾기...")
    free_slots = find_free_slots_for_date(target_date, needed_minutes)

    if not free_slots:
        message = f"""😔 내일({day_name}요일) 캘린더에 빈 시간이 부족해요.

필요한 시간: {needed_hours}시간
내일 집중할 일: {task_text}

일정을 조정하거나 작업 범위를 줄여볼까요?"""
        send_message(message)
        return {
            "target_date": target_date.strftime("%Y-%m-%d"),
            "focus_task": task_text,
            "scope_analysis": scope_result,
            "focus_blocks": []
        }

    print(f"✅ {len(free_slots)}개 빈 시간 발견")

    # Focus Block 생성
    print("\n🔒 Focus Block 생성 중...")
    created_blocks = []
    remaining_minutes = needed_minutes

    for free_start, free_end, gap_minutes in free_slots:
        if remaining_minutes <= 0:
            break

        block_minutes = min(remaining_minutes, gap_minutes)
        start_iso = free_start.isoformat()
        success = create_focus_block(task_text, start_iso, block_minutes)

        if success:
            created_blocks.append({
                "start": start_iso,
                "duration": block_minutes
            })
            remaining_minutes -= block_minutes

    # 요약 메시지 발송
    remaining_hours = remaining_minutes / 60 if remaining_minutes > 0 else 0
    summary = format_focus_summary(
        task_text, scope_result, created_blocks,
        needed_hours, remaining_hours, target_date, day_name
    )
    send_message(summary)

    return {
        "target_date": target_date.strftime("%Y-%m-%d"),
        "focus_task": task_text,
        "scope_analysis": scope_result,
        "focus_blocks": created_blocks
    }


def format_focus_summary(task, scope_result, created_blocks, needed_hours, remaining_hours, target_date, day_name):
    """Focus 요약 메시지 포맷팅"""
    summary = f"""🎯 내일의 Focus
"{task}"

📏 스콥 분석
- 작업 복잡도: {scope_result['complexity']}
- 예상 필요 시간: {scope_result['estimated_hours']}시간
- 분석 근거: {scope_result['reasoning']}
"""

    if scope_result.get('advice'):
        summary += f"\n💡 작업 조언\n{scope_result['advice']}\n"

    if created_blocks:
        total_minutes = sum(block['duration'] for block in created_blocks)
        secured_hours = total_minutes / 60

        if remaining_hours > 0:
            summary += f"\n⚠️ Focus Block 부분 생성\n"
            summary += f"필요: {needed_hours}시간 → 확보: {secured_hours:.1f}시간\n"
        else:
            summary += f"\n🔒 Focus Block 생성 완료!\n"

        summary += f"\n📋 내일({target_date.strftime('%m/%d')} {day_name}) 블록:\n"
        for block in created_blocks:
            start_dt = datetime.fromisoformat(block['start'])
            end_dt = start_dt + timedelta(minutes=block['duration'])
            summary += f"- {start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')} ({block['duration']/60:.1f}시간)\n"

        if remaining_hours > 0:
            summary += f"\n💡 {remaining_hours:.1f}시간 부족\n"
            summary += "일정을 조정하거나, 작업을 나눠서 진행하는 건 어떨까요?\n"
        else:
            summary += "\n이 시간엔 다른 미팅이 끼어들 수 없어요! 집중해봐요 💪"
    else:
        summary += f"\n⚠️ Focus Block을 생성하지 못했습니다\n"
        summary += "내일 빈 시간이 없어요. 일정 조정이 필요할 것 같아요.\n"

    return summary


def main():
    """메인 함수"""
    print("=" * 60)
    print("🌙 나이틀리 워크플로우 시작 (21:00)")
    print("=" * 60)

    # 0. 내일 근무일 계산
    target_date = get_next_workday()
    weekday_names = ['월', '화', '수', '목', '금', '토', '일']
    day_name = weekday_names[target_date.weekday()]
    print(f"\n📅 내일: {target_date.strftime('%Y-%m-%d')} ({day_name}요일)")

    # 1. 그룹 채팅 폴링 리스너 시작
    print("\n🔌 폴링 리스너 시작 중...")
    start_listener()

    # 2. Lark 토큰 체크
    print("\n🔐 Lark 토큰 체크 중...")
    calendar_available = check_lark_token()

    # ============================
    # Part A: 오늘의 회고
    # ============================
    reflection_data = run_reflection()

    # ============================
    # Part B: 내일의 Focus
    # ============================
    tomorrow_data = None
    if calendar_available:
        tomorrow_data = run_tomorrow_focus(target_date)
    else:
        send_message("Lark 캘린더 연동이 안 되어 Focus Block 생성을 건너뛸게요.")

    # ============================
    # 로그 저장
    # ============================
    print("\n💾 로그 저장 중...")
    log_dir = Path.home() / ".daily-focus"
    log_dir.mkdir(exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"{today}.json"

    log_data = {
        "date": today,
        "created_at": datetime.now().isoformat(),
        "reflection": reflection_data,
        "tomorrow_focus": tomorrow_data
    }

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    print(f"💾 로그 저장 완료: {log_file}")

    print("\n" + "=" * 60)
    print("✅ 나이틀리 워크플로우 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
