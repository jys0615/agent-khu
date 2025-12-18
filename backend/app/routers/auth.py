from .. import schemas, crud, auth, models  # models 추가
from ..database import get_db
from ..cache import cache_manager
"""
인증 관련 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from .. import schemas, crud, auth
from ..database import get_db

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)


@router.post("/register", response_model=schemas.TokenResponse)
async def register(
    user_data: schemas.UserRegister,
    db: Session = Depends(get_db)
):
    """회원가입"""
    # 중복 체크
    existing_user = crud.get_user_by_student_id(db, user_data.student_id)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 학번입니다"
        )
    
    # 사용자 생성
    user = crud.create_user(db, user_data.dict())
    
    # 토큰 발급
    access_token = auth.create_access_token(
        data={"sub": user.student_id}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": schemas.UserResponse.from_orm(user)
    }


@router.post("/login", response_model=schemas.TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """로그인"""
    # 사용자 조회
    user = crud.get_user_by_student_id(db, form_data.username)  # username = student_id
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="학번 또는 비밀번호가 올바르지 않습니다"
        )
    
    # 비밀번호 검증
    if not crud.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="학번 또는 비밀번호가 올바르지 않습니다"
        )
    
    # 마지막 로그인 업데이트
    crud.update_last_login(db, user.id)

    # 세션용 도서관 자격 증명 캐시 (TTL 1시간)
    try:
        await cache_manager.connect()
        await cache_manager.set(
            f"library:cred:{user.student_id}",
            {"username": user.student_id, "password": form_data.password},
            ttl=3600,
        )
    except Exception as e:
        print(f"⚠️ library cred cache 실패: {e}")
    
    # 토큰 발급
    access_token = auth.create_access_token(
        data={"sub": user.student_id}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": schemas.UserResponse.from_orm(user)
    }


@router.get("/me", response_model=schemas.UserResponse)
async def get_me(
    current_user: models.User = Depends(auth.get_current_user)
):
    """현재 사용자 정보"""
    return schemas.UserResponse.from_orm(current_user)