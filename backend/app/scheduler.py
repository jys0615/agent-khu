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
CLASSROOM_SCRAPER = "/mcp-servers/classroom-mcp/scrapers/crawl_classrooms.py"


def _reindex_rag_category(category: str):
    """RAG 인덱스 특정 카테고리 재인덱싱 (동기 래퍼)"""
    try:
        import asyncio
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from scripts.index_rag_data import run as run_indexer
        asyncio.run(run_indexer(category))
    except Exception as e:
        print(f"⚠️ RAG 재인덱싱 실패 ({category}): {e}")


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
            if new_count > 0:
                _reindex_rag_category("notice")

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
            if meals:
                _reindex_rag_category("meal")

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
            data = json.loads(result.stdout)
            # 스크래퍼는 {"seats": [...], "success": bool, ...} 형태를 반환
            seats = data.get("seats", []) if isinstance(data, dict) else data
            if seats:
                crud.update_library_seats(db, seats)
                print(f"✅ 도서관 좌석: {len(seats)}개 업데이트")
            else:
                msg = data.get("message", "좌석 정보 없음") if isinstance(data, dict) else "좌석 정보 없음"
                print(f"⚠️ 도서관 좌석 업데이트 건너뜀: {msg}")

    except Exception as e:
        print(f"❌ 도서관 크롤링 에러: {e}")
    finally:
        db.close()


def sync_classrooms():
    """강의실/교수연구실 정보 동기화 (2개월 주기)"""
    print("🔄 강의실/연구실 자동 크롤링 시작...")
    try:
        result = subprocess.run(
            ["python3", CLASSROOM_SCRAPER],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            print(f"✅ 강의실 크롤링 결과: {result.stdout.strip()}")
        else:
            print(f"❌ 강의실 크롤링 실패: {result.stderr}")

    except Exception as e:
        print(f"❌ 강의실 크롤링 에러: {e}")


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
            print("  ✅ 주간 식단표 스크래핑 완료")
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


def shutdown_scheduler():
    """스케줄러 종료"""
    global _scheduler
    if _scheduler and _scheduler.running:
        try:
            _scheduler.shutdown(wait=False)
            print("✅ 스케줄러 종료 완료")
        except Exception as e:
            print(f"⚠️ 스케줄러 종료 중 오류: {e}")

# scheduler.py 맨 아래에 추가 (shutdown_scheduler 함수 뒤)

def warm_cache():
    """Redis 연결 상태 확인

    MCP 툴 캐싱은 main.py 워밍업(curriculum, classroom)과
    tool_executor 레이어(첫 호출 후 자동 캐시)가 담당한다.
    APScheduler 스레드에서 subprocess를 생성하면 uvicorn 메인 루프와
    충돌(Racing with another loop)하므로 MCP 호출을 여기서 하지 않는다.
    """
    print("🔥 캐시 연결 확인...")

    import asyncio
    from .cache import cache_manager

    async def _check():
        await cache_manager.connect()
        print("  ✅ Redis 연결 확인")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_check())
    except Exception as e:
        print(f"⚠️ 캐시 확인 실패: {e}")
    finally:
        loop.close()
        asyncio.set_event_loop(None)


# 전역 스케줄러 인스턴스 — shutdown_scheduler에서 참조
_scheduler: BackgroundScheduler = None  # type: ignore[assignment]


def start_scheduler():
    """스케줄러 시작"""
    global _scheduler
    _scheduler = BackgroundScheduler()

    # 공지사항: 1시간마다
    _scheduler.add_job(
        func=sync_notices,
        trigger=IntervalTrigger(hours=1),
        id='sync_notices_job',
        name='공지사항 자동 크롤링'
    )

    # 학식: 매일 오전 7시, 11시, 오후 5시
    _scheduler.add_job(
        func=sync_meals,
        trigger='cron',
        hour='7,11,17',
        id='sync_meals_job',
        name='학식 메뉴 자동 크롤링'
    )

    # 도서관: 10분마다
    _scheduler.add_job(
        func=sync_library_seats,
        trigger=IntervalTrigger(minutes=10),
        id='sync_library_job',
        name='도서관 좌석 자동 크롤링'
    )

    # 강의실/연구실: 2개월마다
    _scheduler.add_job(
        func=sync_classrooms,
        trigger=IntervalTrigger(days=60),
        id='sync_classrooms_job',
        name='강의실/연구실 자동 크롤링'
    )

    # 졸업요건: 매주 일요일 오전 2시
    _scheduler.add_job(
        func=sync_curriculum,
        trigger='cron',
        day_of_week='6',
        hour=2,
        minute=0,
        id='sync_curriculum_job',
        name='졸업요건 자동 업데이트'
    )

    # 주간 식단표: 매주 월요일 오전 9시
    _scheduler.add_job(
        func=sync_weekly_meal,
        trigger='cron',
        day_of_week='0',
        hour=9,
        minute=0,
        id='sync_weekly_meal_job',
        name='주간 식단표 자동 업데이트'
    )

    # 캐시 워밍업: 1시간마다
    _scheduler.add_job(
        func=warm_cache,
        trigger=IntervalTrigger(hours=1),
        id='warm_cache_job',
        name='캐시 워밍업'
    )

    # 서버 시작 시 즉시 실행
    _scheduler.add_job(func=sync_notices, trigger='date', id='sync_notices_startup')
    _scheduler.add_job(func=sync_meals, trigger='date', id='sync_meals_startup')
    _scheduler.add_job(func=sync_library_seats, trigger='date', id='sync_library_startup')
    _scheduler.add_job(func=sync_weekly_meal, trigger='date', id='sync_weekly_meal_startup')
    _scheduler.add_job(func=warm_cache, trigger='date', id='warm_cache_startup')

    _scheduler.start()
    print("🚀 백그라운드 크롤링 스케줄러 시작")
    print("  - 공지사항: 1시간마다")
    print("  - 학식 메뉴: 07시, 11시, 17시")
    print("  - 도서관 좌석: 10분마다")
    print("  - 강의실/연구실: 2개월마다")
    print("  - 졸업요건: 매주 일요일 오전 2시")
    print("  - 주간 식단표: 매주 월요일 오전 9시")
    print("  - 캐시 워밍업: 1시간마다")