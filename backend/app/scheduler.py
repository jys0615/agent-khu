"""
백그라운드 자동 크롤링 스케줄러

BackgroundScheduler(별도 스레드) → AsyncIOScheduler(uvicorn 이벤트 루프)로 전환:
- sync 작업(subprocess 기반)은 스케줄러가 자동으로 run_in_executor로 위임
- async 작업(scrape_weekly_meal 등)은 await로 직접 실행 — asyncio.run() 충돌 제거
- warm_cache도 async def로 통일, 새 루프 생성 코드 삭제
"""
import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .database import SessionLocal
from . import crud

log = logging.getLogger(__name__)

# 크롤러 경로
NOTICE_SCRAPER = "/mcp-servers/notice-mcp/scrapers/khu_scraper.py"
MEAL_SCRAPER = "/mcp-servers/meal-mcp/scrapers/meal_scraper.py"
LIBRARY_SCRAPER = "/mcp-servers/library-mcp/scrapers/library_scraper.py"
CLASSROOM_SCRAPER = "/mcp-servers/classroom-mcp/scrapers/crawl_classrooms.py"


def _reindex_rag_category(category: str) -> None:
    """RAG 인덱스 특정 카테고리 재인덱싱 (동기 래퍼)"""
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from scripts.index_rag_data import run as run_indexer
        asyncio.run(run_indexer(category))
    except Exception as e:
        log.warning("RAG 재인덱싱 실패 (%s): %s", category, e)


# ── 동기 크롤러 작업 (subprocess 기반 — run_in_executor로 실행됨) ─────────────

def sync_notices() -> None:
    """공지사항 동기화"""
    log.info("공지사항 자동 크롤링 시작...")
    db = SessionLocal()
    try:
        result = subprocess.run(
            ["python3", NOTICE_SCRAPER, "swedu", "20"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            posts = json.loads(result.stdout)
            new_count = sum(1 for post in posts if crud.create_notice_from_mcp(db, post))
            log.info("SW중심대학: %d개 신규 공지", new_count)
            if new_count > 0:
                _reindex_rag_category("notice")
    except Exception as e:
        log.error("공지 크롤링 에러: %s", e)
    finally:
        db.close()


def sync_meals() -> None:
    """학식 메뉴 동기화"""
    log.info("학식 메뉴 자동 크롤링 시작...")
    db = SessionLocal()
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        result = subprocess.run(
            ["python3", MEAL_SCRAPER, today],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            meals = json.loads(result.stdout)
            for meal in meals:
                crud.create_meal(db, meal)
            log.info("학식 메뉴: %d개 업데이트", len(meals))
            if meals:
                _reindex_rag_category("meal")
    except Exception as e:
        log.error("학식 크롤링 에러: %s", e)
    finally:
        db.close()


def sync_library_seats() -> None:
    """도서관 좌석 동기화"""
    log.info("도서관 좌석 자동 크롤링 시작...")
    db = SessionLocal()
    try:
        result = subprocess.run(
            ["python3", LIBRARY_SCRAPER],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            seats = data.get("seats", []) if isinstance(data, dict) else data
            if seats:
                crud.update_library_seats(db, seats)
                log.info("도서관 좌석: %d개 업데이트", len(seats))
            else:
                msg = data.get("message", "좌석 정보 없음") if isinstance(data, dict) else "좌석 정보 없음"
                log.info("도서관 좌석 업데이트 건너뜀: %s", msg)
    except Exception as e:
        log.error("도서관 크롤링 에러: %s", e)
    finally:
        db.close()


def sync_classrooms() -> None:
    """강의실/교수연구실 정보 동기화 (2개월 주기)"""
    log.info("강의실/연구실 자동 크롤링 시작...")
    try:
        result = subprocess.run(
            ["python3", CLASSROOM_SCRAPER],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            log.info("강의실 크롤링 결과: %s", result.stdout.strip())
        else:
            log.error("강의실 크롤링 실패: %s", result.stderr)
    except Exception as e:
        log.error("강의실 크롤링 에러: %s", e)


def sync_curriculum() -> None:
    """졸업요건 동기화"""
    log.info("졸업요건 자동 업데이트 시작: %s", datetime.now())
    try:
        from .routers.curriculum import sync_curriculum_data, load_curriculum_from_mcp

        sync_result = sync_curriculum_data()
        log.info("Sync 결과: %s", sync_result)

        db = SessionLocal()
        try:
            load_result = load_curriculum_from_mcp(db)
            log.info("Load 결과: %s", load_result)
        finally:
            db.close()

        log.info("졸업요건 업데이트 완료: %s", datetime.now())
    except Exception as e:
        log.error("졸업요건 업데이트 실패: %s", e)


# ── 비동기 작업 (이전에는 asyncio.run()으로 새 루프 생성 → 이제 직접 await) ──

async def sync_weekly_meal() -> None:
    """주간 식단표 스크래핑 (매주 월요일 09:00)

    이전: def sync_weekly_meal() + asyncio.run(scrape_weekly_meal()) → 새 루프 생성
    현재: async def → uvicorn 루프에서 직접 await — 루프 충돌 제거
    """
    log.info("주간 식단표 자동 업데이트 시작: %s", datetime.now())
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            log.error("ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다")
            return

        import sys
        sys.path.append("/app/../mcp-servers/meal-mcp")
        from scraper import scrape_weekly_meal  # type: ignore[import]

        result = await scrape_weekly_meal(api_key)  # ← asyncio.run() 대신 await

        if result.get("success"):
            log.info(
                "주간 식단표 완료: week_start=%s, cached_days=%s일",
                result.get("week_start"),
                result.get("cached_days"),
            )
        else:
            log.error("주간 식단표 스크래핑 실패: %s", result.get("message"))
    except Exception as e:
        log.error("주간 식단표 업데이트 실패: %s", e)


async def warm_cache() -> None:
    """Redis 연결 상태 확인

    이전: def warm_cache() + asyncio.new_event_loop() → 불필요한 루프 생성
    현재: async def → uvicorn 루프에서 직접 실행
    """
    log.debug("캐시 연결 확인...")
    try:
        from .cache import cache_manager
        await cache_manager.connect()
        log.debug("Redis 연결 확인 완료")
    except Exception as e:
        log.warning("캐시 확인 실패: %s", e)


# ── 스케줄러 관리 ─────────────────────────────────────────────────────────────

_scheduler: AsyncIOScheduler | None = None  # type: ignore[assignment]


def start_scheduler() -> None:
    """AsyncIOScheduler 시작 (uvicorn 이벤트 루프에 바인딩)"""
    global _scheduler
    _scheduler = AsyncIOScheduler()

    # 공지사항: 1시간마다 (sync → run_in_executor)
    _scheduler.add_job(sync_notices, IntervalTrigger(hours=1),
                       id="sync_notices_job", name="공지사항 자동 크롤링")

    # 학식: 매일 07시, 11시, 17시 (sync → run_in_executor)
    _scheduler.add_job(sync_meals, "cron", hour="7,11,17",
                       id="sync_meals_job", name="학식 메뉴 자동 크롤링")

    # 도서관: 10분마다 (sync → run_in_executor)
    _scheduler.add_job(sync_library_seats, IntervalTrigger(minutes=10),
                       id="sync_library_job", name="도서관 좌석 자동 크롤링")

    # 강의실/연구실: 2개월마다 (sync → run_in_executor)
    _scheduler.add_job(sync_classrooms, IntervalTrigger(days=60),
                       id="sync_classrooms_job", name="강의실/연구실 자동 크롤링")

    # 졸업요건: 매주 일요일 오전 2시 (sync → run_in_executor)
    _scheduler.add_job(sync_curriculum, "cron", day_of_week="6", hour=2, minute=0,
                       id="sync_curriculum_job", name="졸업요건 자동 업데이트")

    # 주간 식단표: 매주 월요일 오전 9시 (async — 직접 await)
    _scheduler.add_job(sync_weekly_meal, "cron", day_of_week="0", hour=9, minute=0,
                       id="sync_weekly_meal_job", name="주간 식단표 자동 업데이트")

    # 캐시 워밍업: 1시간마다 (async — 직접 await)
    _scheduler.add_job(warm_cache, IntervalTrigger(hours=1),
                       id="warm_cache_job", name="캐시 워밍업")

    # 서버 시작 시 즉시 실행
    _scheduler.add_job(sync_notices, "date", id="sync_notices_startup")
    _scheduler.add_job(sync_meals, "date", id="sync_meals_startup")
    _scheduler.add_job(sync_library_seats, "date", id="sync_library_startup")
    _scheduler.add_job(sync_weekly_meal, "date", id="sync_weekly_meal_startup")
    _scheduler.add_job(warm_cache, "date", id="warm_cache_startup")

    _scheduler.start()
    log.info(
        "백그라운드 스케줄러 시작 (AsyncIOScheduler)\n"
        "  - 공지사항: 1시간마다\n"
        "  - 학식 메뉴: 07시, 11시, 17시\n"
        "  - 도서관 좌석: 10분마다\n"
        "  - 강의실/연구실: 2개월마다\n"
        "  - 졸업요건: 매주 일요일 오전 2시\n"
        "  - 주간 식단표: 매주 월요일 오전 9시\n"
        "  - 캐시 워밍업: 1시간마다"
    )


def shutdown_scheduler() -> None:
    """스케줄러 종료"""
    global _scheduler
    if _scheduler and _scheduler.running:
        try:
            _scheduler.shutdown(wait=False)
            log.info("스케줄러 종료 완료")
        except Exception as e:
            log.warning("스케줄러 종료 중 오류: %s", e)
