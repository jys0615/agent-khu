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
    try:
        updated_user = crud.update_user_profile(
            db,
            current_user.id,
            profile_data.dict(exclude_unset=True)
        )
        if not updated_user:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
    except ValueError as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        from fastapi import HTTPException, status
        print(f"프로필 업데이트 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"프로필 수정 중 오류 발생: {str(e)}"
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


@router.get("/graduation-requirements", response_model=schemas.GraduationRequirements)
async def get_graduation_requirements(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    졸업요건 조회 (사용자 로그인 정보 기반)
    
    사용자의 학과, 입학년도를 자동으로 사용하여 졸업요건을 조회합니다.
    """
    from ..agent.tool_executor import process_tool_call
    
    try:
        # Tool executor를 통해 MCP 호출
        result = await process_tool_call(
            tool_name="get_requirements",
            tool_input={},  # program, year 비워서 자동 추출
            current_user=current_user
        )
        
        if result.get("error"):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error")
            )
        
        return {
            "student_id": current_user.student_id,
            "department": current_user.department,
            "admission_year": current_user.admission_year,
            "found": result.get("found"),
            "requirements": result.get("requirements")
        }
    
    except Exception as e:
        from fastapi import HTTPException, status
        print(f"❌ 졸업요건 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"졸업요건 조회 중 오류 발생: {str(e)}"
        )


@router.get("/graduation-progress", response_model=schemas.GraduationProgress)
async def get_graduation_progress(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    졸업요건 진행도 평가 (사용자 로그인 정보 기반)
    
    사용자의 학과, 입학년도, 이수 학점을 기반으로 진행도를 평가합니다.
    """
    from ..agent.tool_executor import process_tool_call
    
    try:
        # 사용자가 이수한 과목 리스트 (나중에 확장 가능)
        # 현재는 completed_credits 기반
        taken_courses = []
        
        # Tool executor를 통해 MCP 호출
        result = await process_tool_call(
            tool_name="evaluate_progress",
            tool_input={
                "taken_courses": taken_courses
            },
            current_user=current_user
        )
        
        if result.get("error"):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error")
            )
        
        return {
            "student_id": current_user.student_id,
            "department": current_user.department,
            "admission_year": current_user.admission_year,
            "completed_credits": current_user.completed_credits or 0,
            "found": result.get("found"),
            "evaluation": result.get("evaluation")
        }
    
    except Exception as e:
        from fastapi import HTTPException, status
        print(f"❌ 졸업요건 진행도 평가 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"진행도 평가 중 오류 발생: {str(e)}"
        )


@router.get("/graduation-status", response_model=schemas.GraduationStatus)
async def get_graduation_status(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    졸업 요건 현황 (통합 조회)
    
    졸업요건 정보와 사용자의 진행도를 함께 조회합니다.
    """
    from ..agent.tool_executor import process_tool_call
    
    try:
        # 1. 졸업요건 조회
        requirements_result = await process_tool_call(
            tool_name="get_requirements",
            tool_input={},
            current_user=current_user
        )
        
        # 2. 진행도 평가
        progress_result = await process_tool_call(
            tool_name="evaluate_progress",
            tool_input={"taken_courses": []},
            current_user=current_user
        )
        
        return {
            "student_id": current_user.student_id,
            "name": current_user.name,
            "department": current_user.department,
            "admission_year": current_user.admission_year,
            "completed_credits": current_user.completed_credits or 0,
            
            # 졸업요건
            "requirements": {
                "found": requirements_result.get("found"),
                "data": requirements_result.get("requirements")
            },
            
            # 진행도
            "progress": {
                "found": progress_result.get("found"),
                "data": progress_result.get("evaluation")
            }
        }
    
    except Exception as e:
        from fastapi import HTTPException, status
        print(f"❌ 졸업 요건 현황 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"졸업 요건 현황 조회 중 오류 발생: {str(e)}"
        )