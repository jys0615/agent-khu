from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional
from datetime import datetime


# 기존 Classroom CRUD...
def get_classroom_by_code(db: Session, code: str) -> Optional[models.Classroom]:
    return db.query(models.Classroom).filter(models.Classroom.code == code).first()


def search_classrooms(db: Session, query: str) -> List[models.Classroom]:
    search_pattern = f"%{query}%"
    return db.query(models.Classroom).filter(
        (models.Classroom.code.ilike(search_pattern)) |
        (models.Classroom.building_name.ilike(search_pattern)) |
        (models.Classroom.room_number.ilike(search_pattern))
    ).all()


def get_all_classrooms(db: Session) -> List[models.Classroom]:
    return db.query(models.Classroom).all()


def create_classroom(db: Session, classroom: schemas.ClassroomCreate) -> models.Classroom:
    db_classroom = models.Classroom(**classroom.dict())
    db.add(db_classroom)
    db.commit()
    db.refresh(db_classroom)
    return db_classroom


# 🆕 Notice CRUD
def get_notice_by_instagram_id(db: Session, instagram_id: str) -> Optional[models.Notice]:
    """Instagram ID로 공지사항 조회"""
    return db.query(models.Notice).filter(
        models.Notice.instagram_id == instagram_id
    ).first()


def get_latest_notices(db: Session, limit: int = 10) -> List[models.Notice]:
    """최신 공지사항 조회"""
    return db.query(models.Notice).filter(
        models.Notice.is_active == True
    ).order_by(
        models.Notice.posted_at.desc()
    ).limit(limit).all()


def search_notices(db: Session, query: str, limit: int = 5) -> List[models.Notice]:
    """공지사항 검색"""
    search_pattern = f"%{query}%"
    return db.query(models.Notice).filter(
        models.Notice.is_active == True,
        (models.Notice.title.ilike(search_pattern)) |
        (models.Notice.content.ilike(search_pattern))
    ).order_by(
        models.Notice.posted_at.desc()
    ).limit(limit).all()


def create_notice(db: Session, notice: schemas.NoticeCreate) -> models.Notice:
    """공지사항 생성"""
    db_notice = models.Notice(**notice.dict())
    db.add(db_notice)
    db.commit()
    db.refresh(db_notice)
    return db_notice


def create_notice_from_instagram(db: Session, instagram_post: dict) -> models.Notice:
    """Instagram 게시물에서 공지사항 생성"""
    # 중복 체크
    existing = get_notice_by_instagram_id(db, instagram_post["id"])
    if existing:
        return existing
    
    # 제목 추출 (첫 줄 또는 첫 50자)
    caption = instagram_post.get("caption", "")
    title = caption.split("\n")[0][:100] if caption else "제목 없음"
    
    notice_data = schemas.NoticeCreate(
        instagram_id=instagram_post["id"],
        shortcode=instagram_post["shortcode"],
        title=title,
        content=caption,
        instagram_url=instagram_post["url"],
        image_url=instagram_post.get("image_url"),
        posted_at=datetime.fromisoformat(instagram_post["posted_at"]),
        account_name="khu_sw.union",
        likes=instagram_post.get("likes"),
        comments=instagram_post.get("comments")
    )
    
    return create_notice(db, notice_data)