from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..agent import chat_with_claude_async
from .. import schemas, crud, agent
from ..database import get_db
from typing import Optional
from ..auth import get_current_user_optional
from .. import models
router = APIRouter(
    prefix="/api",
    tags=["chat"]
)


@router.post("/chat", response_model=schemas.ChatResponse)
async def chat(
    request: schemas.ChatRequest, 
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional)  # 🆕 추가
):
    """채팅 엔드포인트 - 사용자 인증 선택적 지원"""
    try:
        result = await chat_with_claude_async(
            request.message,
            db,
            request.latitude,
            request.longitude,
            request.library_username,
            request.library_password,
            current_user  # 🆕 사용자 정보 전달
        )
        
        # 기본 응답
        response_data = {
            "message": result.get("message", ""),
            "classroom": result.get("classroom"),
            "map_link": result.get("map_link"),
            "show_map_button": result.get("show_map_button", False),
            "notices": result.get("notices"),
            "show_notices": result.get("show_notices", False),
            "meals": result.get("meals"),
            "seats": result.get("seats"),
            "shuttle": result.get("next_bus"),
            "shuttles": result.get("shuttles"),
            "courses": result.get("courses"),
            
            # 🆕 도서관 필드 추가
            "library_info": result.get("library_info"),
            "show_library_info": result.get("show_library_info", False),
            "library_seats": result.get("library_seats"),
            "show_library_seats": result.get("show_library_seats", False),
            "reservation": result.get("reservation"),
            "show_reservation": result.get("show_reservation", False),
            "needs_library_login": result.get("needs_library_login", False),
                        # 🆕 도서관 예약 링크 추가
            "library_reservation_url": result.get("library_reservation_url"),
            "show_reservation_button": result.get("show_reservation_button", False),
            
            # 🆕 교과과정 필드
            "requirements": result.get("requirements"),
            "show_requirements": result.get("show_requirements", False),
            "evaluation": result.get("evaluation"),
            "show_evaluation": result.get("show_evaluation", False),
            "curriculum_courses": result.get("curriculum_courses")
        }
        
        return response_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/classrooms", response_model=List[schemas.ClassroomInfo])
async def get_classrooms(db: Session = Depends(get_db)):
    """
    모든 강의실 목록 조회
    """
    classrooms = crud.get_all_classrooms(db)
    return classrooms


@router.get("/classrooms/{code}", response_model=schemas.ClassroomInfo)
async def get_classroom(code: str, db: Session = Depends(get_db)):
    """
    특정 강의실 정보 조회
    """
    classroom = crud.get_classroom_by_code(db, code)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    return classroom