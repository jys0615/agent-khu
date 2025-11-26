"""
프로필 관련 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas, crud, auth, models
from ..database import get_db

router = APIRouter(
    prefix="/api/profiles",
    tags=["profiles"]
)


@router.get("/me", response_model=schemas.UserResponse)
async def get_my_profile(
    current_user: models.User = Depends(auth.get_current_user)
):
    """내 프로필 조회"""
    return schemas.UserResponse.from_orm(current_user)


@router.put("/me", response_model=schemas.UserResponse)
async def update_my_profile(
    profile_data: schemas.ProfileUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """프로필 수정"""
    updated_user = crud.update_user_profile(
        db,
        current_user.id,
        profile_data.dict(exclude_unset=True)
    )
    
    return schemas.UserResponse.from_orm(updated_user)


@router.post("/setup", response_model=schemas.UserResponse)
async def setup_profile(
    profile_data: schemas.ProfileSetup,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """최초 프로필 설정"""
    updated_user = crud.update_user_profile(
        db,
        current_user.id,
        profile_data.dict(exclude_unset=True)
    )
    
    return schemas.UserResponse.from_orm(updated_user)


@router.get("/graduation-status")
async def get_graduation_status(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """졸업 요건 현황"""
    # Curriculum에서 졸업요건 조회
    curriculum = crud.get_curriculum(
        db,
        current_user.department,
        current_user.admission_year
    )
    
    if not curriculum:
        return {
            "message": f"{current_user.admission_year}학번 {current_user.department} 졸업요건 정보가 없습니다"
        }
    
    import json
    requirements = json.loads(curriculum.requirements)
    
    # 진행 상황 계산
    completed = current_user.completed_credits or 0
    total = requirements.get("total_credits", 130)
    
    return {
        "department": current_user.department,
        "admission_year": current_user.admission_year,
        "completed_credits": completed,
        "total_credits": total,
        "progress_percentage": round((completed / total) * 100, 1),
        "requirements": requirements
    }