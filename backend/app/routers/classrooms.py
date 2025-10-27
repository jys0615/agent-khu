"""
강의실 관련 라우터
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/api/classrooms",
    tags=["classrooms"]
)


@router.get("/search", response_model=List[schemas.ClassroomInfo])  # 수정
async def search_classrooms(
    q: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """강의실 검색"""
    classrooms = crud.search_classrooms(db, q, limit)
    
    if not classrooms:
        raise HTTPException(status_code=404, detail="강의실을 찾을 수 없습니다")
    
    return classrooms


@router.get("/stats/summary")
async def get_classroom_stats(db: Session = Depends(get_db)):
    """강의실 통계"""
    stats = crud.get_classroom_stats(db)
    return stats


@router.get("/{classroom_id}", response_model=schemas.ClassroomInfo)  # 수정
async def get_classroom(classroom_id: int, db: Session = Depends(get_db)):
    """강의실 상세 정보"""
    classroom = crud.get_classroom(db, classroom_id)
    
    if not classroom:
        raise HTTPException(status_code=404, detail="강의실을 찾을 수 없습니다")
    
    return classroom