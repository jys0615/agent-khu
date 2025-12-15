"""
백그라운드 자동 크롤링 스케줄러
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .database import SessionLocal
from . import crud
import subprocess
import json
import os
import asyncio
from datetime import datetime

# 크롤러 경로
NOTICE_SCRAPER = "/mcp-servers/notice-mcp/scrapers/khu_scraper.py"
MEAL_SCRAPER = "/mcp-servers/meal-mcp/scrapers/meal_scraper.py"
LIBRARY_SCRAPER = "/mcp-servers/library-mcp/scrapers/library_scraper.py"


def sync_notices():
    """공지사항 동기화"""
    print("🔄 공지사항 자동 크롤링 시작...")
    db = SessionLocal()
    
    try:
        result = subprocess.run(
            ["python3", NOTICE_SCRAPER, "swedu", "20"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            posts = json.loads(result.stdout)
            new_count = sum(1 for post in posts if crud.create_notice_from_mcp(db, post))
            print(f"✅ SW중심대학: {new_count}개 신규 공지")
        
    except Exception as e:
        print(f"❌ 공지 크롤링 에러: {e}")
    finally:
        db.close()


def sync_meals():
    """학식 메뉴 동기화"""
    print("🔄 학식 메뉴 자동 크롤링 시작...")
    db = SessionLocal()
    
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        result = subprocess.run(
            ["python3", MEAL_SCRAPER, today],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            meals = json.loads(result.stdout)
            for meal in meals:
                crud.create_meal(db, meal)
            print(f"✅ 학식 메뉴: {len(meals)}개 업데이트")
        
    except Exception as e:
        print(f"❌ 학식 크롤링 에러: {e}")
    finally:
        db.close()


def sync_library_seats():
    """도서관 좌석 동기화"""
    print("🔄 도서관 좌석 자동 크롤링 시작...")
    db = SessionLocal()
    
    try:
        result = subprocess.run(
            ["python3", LIBRARY_SCRAPER],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            seats = json.loads(result.stdout)
            crud.update_library_seats(db, seats)
            print(f"✅ 도서관 좌석: {len(seats)}개 업데이트")
        
    except Exception as e:
        print(f"❌ 도서관 크롤링 에러: {e}")
    finally:
        db.close()


def sync_curriculum():
    """졸업요건 동기화"""
    print("\n" + "="*60)
    print(f"🔄 졸업요건 자동 업데이트 시작: {datetime.now()}")
    print("="*60)
    
    try:
        from .routers.curriculum import sync_curriculum_data, load_curriculum_from_mcp
        
        # 1. MCP 데이터 동기화
        sync_result = sync_curriculum_data()
        print(f"  📡 Sync 결과: {sync_result}")
        
        # 2. DB에 저장
        db = SessionLocal()
        try:
            load_result = load_curriculum_from_mcp(db)
            print(f"  💾 Load 결과: {load_result}")
        finally:
            db.close()
        
        print(f"✅ 졸업요건 업데이트 완료: {datetime.now()}")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"❌ 졸업요건 업데이트 실패: {e}")
        import traceback
        traceback.print_exc()


def sync_weekly_meal():
    """주간 식단표 스크래핑 (매주 월요일 09:00)"""
    print("\n" + "="*60)
    print(f"🍽️  주간 식단표 자동 업데이트 시작: {datetime.now()}")
    print("="*60)
    
    try:
        # 환경변수에서 API 키 가져오기
        api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            print("  ❌ ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다")
            return
        
        # scraper 직접 호출
        import sys
        sys.path.append("/app/../mcp-servers/meal-mcp")
        
        from scraper import scrape_weekly_meal
        
        # asyncio.run으로 비동기 함수 실행
        result = asyncio.run(scrape_weekly_meal(api_key))
        
        if result.get("success"):
            print(f"  ✅ 주간 식단표 스크래핑 완료")
            print(f"  📅 주간 시작: {result.get('week_start')}")
            print(f"  📦 캐시된 일수: {result.get('cached_days')}일")
        else:
            print(f"  ❌ 스크래핑 실패: {result.get('message')}")
        
        print(f"✅ 주간 식단표 업데이트 완료: {datetime.now()}")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"❌ 주간 식단표 업데이트 실패: {e}")
        import traceback
        traceback.print_exc()


def start_scheduler():
    """스케줄러 시작"""
    scheduler = BackgroundScheduler()
    
    # 공지사항: 1시간마다
    scheduler.add_job(
        func=sync_notices,
        trigger=IntervalTrigger(hours=1),
        id='sync_notices_job',
        name='공지사항 자동 크롤링'
    )
    
    # 학식: 매일 오전 7시, 11시, 오후 5시
    scheduler.add_job(
        func=sync_meals,
        trigger='cron',
        hour='7,11,17',
        id='sync_meals_job',
        name='학식 메뉴 자동 크롤링'
    )
    
    # 도서관: 10분마다 (시험 기간에는 더 자주)
    scheduler.add_job(
        func=sync_library_seats,
        trigger=IntervalTrigger(minutes=10),
        id='sync_library_job',
        name='도서관 좌석 자동 크롤링'
    )
    
    # 졸업요건: 매주 일요일 오전 2시
    scheduler.add_job(
        func=sync_curriculum,
        trigger='cron',
        day_of_week='6',  # 일요일
        hour=2,
        minute=0,
        id='sync_curriculum_job',
        name='졸업요건 자동 업데이트'
    )
    
    # 주간 식단표: 매주 월요일 오전 9시
    scheduler.add_job(
        func=sync_weekly_meal,
        trigger='cron',
        day_of_week='0',  # 월요일
        hour=9,
        minute=0,
        id='sync_weekly_meal_job',
        name='주간 식단표 자동 업데이트'
    )
    
    # 서버 시작 시 즉시 실행
    scheduler.add_job(func=sync_notices, trigger='date', id='sync_notices_startup')
    scheduler.add_job(func=sync_meals, trigger='date', id='sync_meals_startup')
    scheduler.add_job(func=sync_library_seats, trigger='date', id='sync_library_startup')
    scheduler.add_job(func=sync_weekly_meal, trigger='date', id='sync_weekly_meal_startup')  # 주간 식단표도 서버 시작 시 실행
    
    scheduler.start()
    print("🚀 백그라운드 크롤링 스케줄러 시작")
    print("  - 공지사항: 1시간마다")
    print("  - 학식 메뉴: 07시, 11시, 17시")
    print("  - 도서관 좌석: 10분마다")
    print("  - 졸업요건: 매주 일요일 오전 2시")
    print("  - 주간 식단표: 매주 월요일 오전 9시 ⭐ NEW")


def shutdown_scheduler():
    """스케줄러 종료"""
    try:
        scheduler.shutdown(wait=False)
        print("✅ 스케줄러 종료 완료")
    except Exception as e:
        print(f"⚠️ 스케줄러 종료 중 오류: {e}")