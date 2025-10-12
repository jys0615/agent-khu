from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, crud, agent
from ..database import get_db

router = APIRouter(
    prefix="/api",
    tags=["chat"]
)


@router.post("/chat", response_model=schemas.ChatResponse)
async def chat(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    """
    채팅 API - OpenAI Agent를 통해 강의실 정보 및 공지사항 제공
    """
    try:
        (
            ai_message, 
            classroom_info, 
            map_link, 
            show_map_button,
            notices,  # 🆕
            show_notices  # 🆕
        ) = await agent.chat_with_agent(
            db=db,
            user_message=request.message,
            user_lat=request.user_latitude,
            user_lon=request.user_longitude
        )
        
        return schemas.ChatResponse(
            message=ai_message,
            classroom_info=classroom_info,
            map_link=map_link,
            show_map_button=show_map_button,
            notices=notices,  # 🆕
            show_notices=show_notices  # 🆕
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/classrooms", response_model=List[schemas.Classroom])
async def get_classrooms(db: Session = Depends(get_db)):
    """
    모든 강의실 목록 조회
    """
    classrooms = crud.get_all_classrooms(db)
    return classrooms


@router.get("/classrooms/{code}", response_model=schemas.Classroom)
async def get_classroom(code: str, db: Session = Depends(get_db)):
    """
    특정 강의실 정보 조회
    """
    classroom = crud.get_classroom_by_code(db, code)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    return classroom