"""
강의실 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import schemas, crud
from ..database import get_db

router = APIRouter(
    prefix="/api/classrooms",
    tags=["classrooms"]
)


@router.get("", response_model=List[schemas.Classroom])
async def get_classrooms(
    skip: int = 0,
    limit: int = 100,
    room_type: Optional[str] = Query(None, description="공간 유형 필터 (classroom, professor_office, lab 등)"),
    floor: Optional[str] = Query(None, description="층 필터 (B, 1, 2, 3, 4)"),
    accessible_only: bool = Query(False, description="학생 접근 가능 공간만"),
    db: Session = Depends(get_db)
):
    """
    강의실/공간 목록 조회
    
    - **room_type**: classroom, professor_office, lab, admin_office, student_council, seminar_room, amenity, restroom
    - **floor**: B(지하), 1, 2, 3, 4
    - **accessible_only**: True로 설정 시 학생 접근 가능한 공간만
    """
    classrooms = crud.get_classrooms(
        db, 
        skip=skip, 
        limit=limit, 
        room_type=room_type, 
        floor=floor, 
        accessible_only=accessible_only
    )
    return classrooms


@router.get("/search", response_model=List[schemas.Classroom])
async def search_classrooms(
    q: str = Query(..., description="검색 키워드 (강의실 번호, 교수님 이름, 공간명 등)"),
    limit: int = Query(10, description="결과 개수"),
    db: Session = Depends(get_db)
):
    """
    강의실/공간 검색
    
    **검색 가능:**
    - 강의실 번호: "101", "전101", "B08"
    - 교수님 이름: "조진성", "홍충선"
    - 공간명: "학생회", "매점", "세미나실"
    - 키워드: "강의실", "연구실", "화장실"
    
    **예시:**
    - `/api/classrooms/search?q=조진성` → 조진성 교수 연구실
    - `/api/classrooms/search?q=매점` → 휴게실(매점)
    - `/api/classrooms/search?q=학생회` → 학생회실들
    """
    classrooms = crud.search_classrooms(db, q, limit)
    return classrooms


@router.get("/professor/{professor_name}", response_model=List[schemas.Classroom])
async def get_professor_office(
    professor_name: str,
    db: Session = Depends(get_db)
):
    """
    교수님 이름으로 연구실 검색
    
    **예시:**
    - `/api/classrooms/professor/조진성`
    - `/api/classrooms/professor/홍충선`
    """
    classrooms = crud.get_classrooms_by_professor(db, professor_name)
    
    if not classrooms:
        raise HTTPException(status_code=404, detail=f"{professor_name} 교수님의 연구실을 찾을 수 없습니다.")
    
    return classrooms


@router.get("/{classroom_code}", response_model=schemas.Classroom)
async def get_classroom(
    classroom_code: str,
    db: Session = Depends(get_db)
):
    """
    특정 강의실/공간 조회
    
    **예시:**
    - `/api/classrooms/전101`
    - `/api/classrooms/101`
    - `/api/classrooms/B08`
    """
    classroom = crud.get_classroom_by_code(db, classroom_code)
    
    if not classroom:
        raise HTTPException(status_code=404, detail=f"{classroom_code}를 찾을 수 없습니다.")
    
    return classroom


@router.get("/stats/summary")
async def get_stats(db: Session = Depends(get_db)):
    """
    공간 통계 정보
    """
    from ..models import Classroom
    
    total = db.query(Classroom).count()
    
    stats = {
        "total": total,
        "by_type": {},
        "by_floor": {},
        "accessible": db.query(Classroom).filter(Classroom.is_accessible == True).count()
    }
    
    # 유형별 통계
    room_types = ['classroom', 'professor_office', 'lab', 'admin_office', 'student_council', 
                  'seminar_room', 'amenity', 'restroom', 'club_room', 'facility', 'utility', 'other']
    
    for room_type in room_types:
        count = db.query(Classroom).filter(Classroom.room_type == room_type).count()
        if count > 0:
            stats['by_type'][room_type] = count
    
    # 층별 통계
    floors = ['B', '1', '2', '3', '4']
    for floor in floors:
        count = db.query(Classroom).filter(Classroom.floor == floor).count()
        if count > 0:
            stats['by_floor'][floor] = count
    
    return stats