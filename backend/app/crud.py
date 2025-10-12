"""
데이터베이스 CRUD 작업
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from . import models, schemas
from typing import List, Optional


# ========== 강의실/공간 관련 ==========

def get_classroom_by_code(db: Session, code: str) -> Optional[models.Classroom]:
    """
    강의실 코드로 조회
    예: "전101", "101", "B08" 등
    """
    # 다양한 형태의 입력 처리
    search_codes = [code]
    
    # "전101" -> "101"도 검색
    if code.startswith("전"):
        search_codes.append(code[1:])
    # "101" -> "전101"도 검색
    else:
        search_codes.append(f"전{code}")
    
    return db.query(models.Classroom).filter(
        or_(
            models.Classroom.code.in_(search_codes),
            models.Classroom.room_number.in_(search_codes)
        )
    ).first()


def get_classrooms(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    room_type: Optional[str] = None,
    floor: Optional[str] = None,
    accessible_only: bool = False
) -> List[models.Classroom]:
    """
    강의실 목록 조회 (필터링 지원)
    """
    query = db.query(models.Classroom)
    
    if room_type:
        query = query.filter(models.Classroom.room_type == room_type)
    
    if floor:
        query = query.filter(models.Classroom.floor == floor)
    
    if accessible_only:
        query = query.filter(models.Classroom.is_accessible == True)
    
    return query.offset(skip).limit(limit).all()


def search_classrooms(
    db: Session,
    query: str,
    limit: int = 10
) -> List[models.Classroom]:
    """
    강의실/공간 검색 (키워드, 교수님 이름, 공간명 등)
    """
    search_pattern = f"%{query}%"
    
    return db.query(models.Classroom).filter(
        or_(
            models.Classroom.code.ilike(search_pattern),
            models.Classroom.room_name.ilike(search_pattern),
            models.Classroom.professor_name.ilike(search_pattern),
            models.Classroom.keywords.ilike(search_pattern)
        )
    ).limit(limit).all()


def get_classrooms_by_professor(db: Session, professor_name: str) -> List[models.Classroom]:
    """
    교수님 이름으로 연구실 검색
    """
    return db.query(models.Classroom).filter(
        models.Classroom.professor_name.ilike(f"%{professor_name}%")
    ).all()


# ========== 공지사항 관련 ==========

def get_latest_notices(
    db: Session,
    source: Optional[str] = None,
    limit: int = 10
) -> List[models.Notice]:
    """
    최신 공지사항 조회
    """
    query = db.query(models.Notice).filter(models.Notice.is_active == True)
    
    if source:
        query = query.filter(models.Notice.source == source)
    
    return query.order_by(models.Notice.crawled_at.desc()).limit(limit).all()


def search_notices(
    db: Session,
    query: str,
    limit: int = 10
) -> List[models.Notice]:
    """
    공지사항 검색
    """
    search_pattern = f"%{query}%"
    
    return db.query(models.Notice).filter(
        and_(
            models.Notice.is_active == True,
            or_(
                models.Notice.title.ilike(search_pattern),
                models.Notice.content.ilike(search_pattern)
            )
        )
    ).order_by(models.Notice.crawled_at.desc()).limit(limit).all()


def create_notice_from_mcp(db: Session, notice_data: dict) -> Optional[models.Notice]:
    """
    MCP에서 받은 공지사항 데이터 저장
    """
    # 중복 체크
    existing = db.query(models.Notice).filter(
        models.Notice.notice_id == notice_data.get("id")
    ).first()
    
    if existing:
        return None
    
    # 새 공지사항 생성
    notice = models.Notice(
        notice_id=notice_data.get("id"),
        source=notice_data.get("source", "unknown"),
        title=notice_data.get("title", ""),
        content=notice_data.get("content", ""),
        url=notice_data.get("url", ""),
        date=notice_data.get("date", ""),
        author=notice_data.get("author"),
        views=notice_data.get("views", 0)
    )
    
    db.add(notice)
    db.commit()
    db.refresh(notice)
    
    return notice