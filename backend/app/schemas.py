import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator

class ClassroomInfo(BaseModel):
    code: str
    building_name: str
    room_number: str
    floor: str
    room_name: str
    room_type: str
    professor_name: Optional[str] = None
    is_accessible: bool = True
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class NoticeInfo(BaseModel):
    title: str
    url: str
    date: str
    author: Optional[str]
    source: str
    views: Optional[int]

class MealInfo(BaseModel):
    cafeteria: str
    meal_type: str
    menu: str
    price: int
    menu_url: Optional[str] = None
    source_url: Optional[str] = None

class SeatInfo(BaseModel):
    location: str
    floor: Optional[str]
    total: int
    available: int
    usage_rate: float

class ShuttleInfo(BaseModel):
    route: str
    departure: str
    arrival: str
    next_time: Optional[str]
    note: Optional[str]
    weekday_times: Optional[List[str]]
    weekend_times: Optional[List[str]]

class CourseInfo(BaseModel):
    code: str
    name: str
    professor: str
    credits: int
    time: str
    classroom: str
    classification: str

class ChatResponse(BaseModel):
    message: str
    classroom: Optional[ClassroomInfo] = None
    map_link: Optional[str] = None
    show_map_button: bool = False
    notices: Optional[List[NoticeInfo]] = None
    show_notices: bool = False
    meals: Optional[List[MealInfo]] = None
    seats: Optional[List[SeatInfo]] = None
    shuttle: Optional[ShuttleInfo] = None
    shuttles: Optional[List[ShuttleInfo]] = None
    courses: Optional[List[CourseInfo]] = None
    
    # 🆕 도서관 관련 필드
    library_info: Optional[Dict[str, Any]] = None
    show_library_info: bool = False
    library_seats: Optional[Dict[str, Any]] = None
    show_library_seats: bool = False
    reservation: Optional[Dict[str, Any]] = None
    show_reservation: bool = False
    needs_library_login: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
        # 🆕 도서관 예약 링크 추가
    library_reservation_url: Optional[str] = None
    show_reservation_button: bool = False
    
    # 🆕 교과과정 관련 필드 (기존)
    requirements: Optional[Dict[str, Any]] = None
    show_requirements: bool = False
    evaluation: Optional[Dict[str, Any]] = None
    show_evaluation: bool = False
    curriculum_courses: Optional[List[Dict[str, Any]]] = None

# 회원가입 요청
class UserRegister(BaseModel):
    student_id: str  # 학번
    password: str
    department: str  # 학과
    campus: str  # 캠퍼스
    name: Optional[str] = None
    admission_year: Optional[int] = None
    is_transfer: bool = False
    transfer_year: Optional[int] = None
    double_major: Optional[str] = None
    minor: Optional[str] = None
    
    @validator('student_id')
    def validate_student_id(cls, v):
        if not v.isdigit() or len(v) != 10:
            raise ValueError('학번은 10자리 숫자여야 합니다')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('비밀번호는 최소 8자 이상이어야 합니다')
        return v
    
    @validator('campus')
    def validate_campus(cls, v):
        if v not in ['국제캠퍼스', '서울캠퍼스']:
            raise ValueError('올바른 캠퍼스를 선택하세요')
        return v

    @validator('admission_year')
    def validate_admission_year(cls, v, values):
        if v is None:
            # 학번에서 자동 추출
            student_id = values.get('student_id', '')
            if student_id and student_id.isdigit() and len(student_id) >= 4:
                return int(student_id[:4])
            return v
        if v < 2000 or v > 2100:
            raise ValueError('올바른 입학년도를 입력하세요')
        return v


# 로그인 요청
class UserLogin(BaseModel):
    student_id: str
    password: str


# 프로필 설정 (선택사항)
class ProfileSetup(BaseModel):
    current_grade: Optional[int] = None
    interests: Optional[List[str]] = None
    completed_credits: Optional[int] = None
    double_major: Optional[str] = None
    minor: Optional[str] = None
    name: Optional[str] = None
    campus: Optional[str] = None
    admission_year: Optional[int] = None
    student_id: Optional[str] = None
    is_transfer: Optional[bool] = None
    transfer_year: Optional[int] = None

    @validator('student_id')
    def validate_student_id(cls, v):
        if v is None:
            return v
        if not v.isdigit() or len(v) != 10:
            raise ValueError('학번은 10자리 숫자여야 합니다')
        return v
    
    @validator('campus')
    def validate_campus(cls, v):
        if v is None:
            return v
        if v not in ['국제캠퍼스', '서울캠퍼스']:
            raise ValueError('올바른 캠퍼스를 선택하세요')
        return v
    
    @validator('admission_year')
    def validate_admission_year(cls, v):
        if v is None:
            return v
        if v < 2000 or v > 2100:
            raise ValueError('올바른 입학년도를 입력하세요')
        return v


# 프로필 수정
class ProfileUpdate(BaseModel):
    current_grade: Optional[int] = None
    interests: Optional[List[str]] = None
    completed_credits: Optional[int] = None
    double_major: Optional[str] = None
    minor: Optional[str] = None
    preferences: Optional[dict] = None
    name: Optional[str] = None
    campus: Optional[str] = None
    admission_year: Optional[int] = None
    student_id: Optional[str] = None
    is_transfer: Optional[bool] = None
    transfer_year: Optional[int] = None

    @validator('student_id')
    def validate_student_id(cls, v):
        if v is None:
            return v
        if not v.isdigit() or len(v) != 10:
            raise ValueError('학번은 10자리 숫자여야 합니다')
        return v
    
    @validator('campus')
    def validate_campus(cls, v):
        if v is None:
            return v
        if v not in ['국제캠퍼스', '서울캠퍼스']:
            raise ValueError('올바른 캠퍼스를 선택하세요')
        return v
    
    @validator('admission_year')
    def validate_admission_year(cls, v):
        if v is None:
            return v
        if v < 2000 or v > 2100:
            raise ValueError('올바른 입학년도를 입력하세요')
        return v


# 사용자 응답 (민감정보 제외)
class UserResponse(BaseModel):
    id: int
    student_id: str
    name: Optional[str]
    department: str
    campus: str
    admission_year: int
    is_transfer: bool
    transfer_year: Optional[int]
    current_grade: Optional[int]
    interests: Optional[List[str]]
    completed_credits: Optional[int]
    double_major: Optional[str]
    minor: Optional[str]
    
    class Config:
        orm_mode = True
    
    @classmethod
    def from_orm(cls, obj):
        # JSON 필드 파싱
        interests = None
        if obj.interests:
            try:
                interests = json.loads(obj.interests)
            except (json.JSONDecodeError, TypeError):
                pass
        
        return cls(
            id=obj.id,
            student_id=obj.student_id,
            name=obj.name,
            department=obj.department,
            campus=obj.campus,
            admission_year=obj.admission_year,
            is_transfer=obj.is_transfer,
            transfer_year=obj.transfer_year,
            current_grade=obj.current_grade,
            interests=interests,
            completed_credits=obj.completed_credits,
            double_major=obj.double_major,
            minor=obj.minor
        )


# 토큰 응답
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ChatRequest 수정 (기존 것 수정)
class ChatRequest(BaseModel):
    message: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    library_username: Optional[str] = None
    library_password: Optional[str] = None
    # 토큰은 헤더로 받을 예정 (Authorization: Bearer <token>)


# ========== 졸업요건 관련 응답 스키마 ==========

class GraduationRequirements(BaseModel):
    """졸업요건 정보"""
    student_id: str
    department: str
    admission_year: int
    found: bool
    requirements: Optional[Dict[str, Any]] = None


class GraduationProgress(BaseModel):
    """졸업 진행도 평가"""
    student_id: str
    department: str
    admission_year: int
    completed_credits: int
    found: bool
    evaluation: Optional[Dict[str, Any]] = None


class GraduationStatus(BaseModel):
    """졸업 요건 통합 현황 (requirements + progress)"""
    student_id: str
    name: Optional[str]
    department: str
    admission_year: int
    completed_credits: int
    
    # 졸업요건
    requirements: Dict[str, Any] = {
        "found": False,
        "data": None
    }
    
    # 진행도
    progress: Dict[str, Any] = {
        "found": False,
        "data": None
    }