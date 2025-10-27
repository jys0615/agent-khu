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
from datetime import datetime

# 크롤러 경로
NOTICE_SCRAPER = os.path.expanduser("~/Desktop/agent-khu/mcp-servers/notice-mcp/scrapers/khu_scraper.py")
MEAL_SCRAPER = os.path.expanduser("~/Desktop/agent-khu/mcp-servers/meal-mcp/scrapers/meal_scraper.py")
LIBRARY_SCRAPER = os.path.expanduser("~/Desktop/agent-khu/mcp-servers/library-mcp/scrapers/library_scraper.py")


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
    
    # 서버 시작 시 즉시 실행
    scheduler.add_job(func=sync_notices, trigger='date', id='sync_notices_startup')
    scheduler.add_job(func=sync_meals, trigger='date', id='sync_meals_startup')
    scheduler.add_job(func=sync_library_seats, trigger='date', id='sync_library_startup')
    
    scheduler.start()
    print("🚀 백그라운드 크롤링 스케줄러 시작")
    print("  - 공지사항: 1시간마다")
    print("  - 학식 메뉴: 07시, 11시, 17시")
    print("  - 도서관 좌석: 10분마다")