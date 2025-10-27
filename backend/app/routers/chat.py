from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..agent import chat_with_claude_async  # 변경!
from .. import schemas, crud, agent
from ..database import get_db

router = APIRouter(
    prefix="/api",
    tags=["chat"]
)


@router.post("/chat", response_model=schemas.ChatResponse)
async def chat(request: schemas.ChatRequest, db: Session = Depends(get_db)):  # async 추가!
    """채팅 엔드포인트"""
    try:
        result = await chat_with_claude_async(  # await 추가!
            request.message,
            db,
            request.latitude,
            request.longitude
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
            "courses": result.get("courses")
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