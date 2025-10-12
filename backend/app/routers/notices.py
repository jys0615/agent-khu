"""
공지사항 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import subprocess
import json
import os

from .. import schemas, crud
from ..database import get_db

router = APIRouter(
    prefix="/api/notices",
    tags=["notices"]
)

# Python 스크립트 경로
SCRAPER_PATH = os.path.expanduser("~/Desktop/agent-khu/mcp-servers/khu-notice-mcp/scrapers/khu_scraper.py")


def run_scraper(source: str, limit: int = 20) -> List[dict]:
    """
    Python 크롤러 스크립트 직접 실행
    """
    try:
        result = subprocess.run(
            ["/Library/Frameworks/Python.framework/Versions/3.12/bin/python3", 
             SCRAPER_PATH, source, str(limit)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise Exception(f"Scraper failed: {result.stderr}")
        
        notices = json.loads(result.stdout)
        return notices
    
    except subprocess.TimeoutExpired:
        raise Exception("Scraper timeout")
    except json.JSONDecodeError as e:
        raise Exception(f"JSON parse error: {e}\nOutput: {result.stdout}")
    except Exception as e:
        raise Exception(f"Scraper error: {str(e)}")


@router.get("", response_model=List[schemas.Notice])
async def get_notices(
    source: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    최신 공지사항 목록 조회
    source: swedu, department, schedule (선택)
    """
    notices = crud.get_latest_notices(db, source=source, limit=limit)
    return notices


@router.get("/search", response_model=List[schemas.Notice])
async def search_notices(
    query: str,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    공지사항 검색
    """
    notices = crud.search_notices(db, query=query, limit=limit)
    return notices


@router.post("/sync/swedu", response_model=dict)
async def sync_sw_notices(
    force_refresh: bool = False,
    db: Session = Depends(get_db)
):
    """
    SW중심대학사업단 공지사항 동기화
    """
    try:
        notices = run_scraper("swedu", 20)
        
        created_count = 0
        for notice in notices:
            db_notice = crud.create_notice_from_mcp(db, notice)
            if db_notice:
                created_count += 1
        
        return {
            "status": "success",
            "source": "swedu",
            "fetched": len(notices),
            "created": created_count,
            "message": f"SW사업단 {len(notices)}개의 공지사항 중 {created_count}개가 새로 추가되었습니다."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/department", response_model=dict)
async def sync_department_notices(
    force_refresh: bool = False,
    db: Session = Depends(get_db)
):
    """
    소프트웨어융합대학 공지사항 동기화
    """
    try:
        notices = run_scraper("department", 20)
        
        created_count = 0
        for notice in notices:
            db_notice = crud.create_notice_from_mcp(db, notice)
            if db_notice:
                created_count += 1
        
        return {
            "status": "success",
            "source": "department",
            "fetched": len(notices),
            "created": created_count,
            "message": f"학과 {len(notices)}개의 공지사항 중 {created_count}개가 새로 추가되었습니다."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/schedule", response_model=dict)
async def sync_schedule(
    force_refresh: bool = False,
    db: Session = Depends(get_db)
):
    """
    학사일정 동기화
    """
    try:
        schedules = run_scraper("schedule", 50)
        
        created_count = 0
        for schedule in schedules:
            db_schedule = crud.create_notice_from_mcp(db, schedule)
            if db_schedule:
                created_count += 1
        
        return {
            "status": "success",
            "source": "schedule",
            "fetched": len(schedules),
            "created": created_count,
            "message": f"학사일정 {len(schedules)}개 항목 중 {created_count}개가 새로 추가되었습니다."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/all", response_model=dict)
async def sync_all_notices(
    force_refresh: bool = False,
    db: Session = Depends(get_db)
):
    """
    모든 공지사항 동기화
    """
    try:
        total_fetched = 0
        total_created = 0
        
        # SW사업단
        sw_notices = run_scraper("swedu", 20)
        for notice in sw_notices:
            if crud.create_notice_from_mcp(db, notice):
                total_created += 1
        total_fetched += len(sw_notices)
        
        # 학과
        dept_notices = run_scraper("department", 20)
        for notice in dept_notices:
            if crud.create_notice_from_mcp(db, notice):
                total_created += 1
        total_fetched += len(dept_notices)
        
        # 학사일정
        schedules = run_scraper("schedule", 50)
        for schedule in schedules:
            if crud.create_notice_from_mcp(db, schedule):
                total_created += 1
        total_fetched += len(schedules)
        
        return {
            "status": "success",
            "fetched": total_fetched,
            "created": total_created,
            "message": f"전체 {total_fetched}개의 공지사항 중 {total_created}개가 새로 추가되었습니다."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{notice_id}", response_model=schemas.Notice)
async def get_notice(
    notice_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 공지사항 조회
    """
    from ..models import Notice
    notice = db.query(Notice).filter(Notice.id == notice_id).first()
    
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    
    return notice