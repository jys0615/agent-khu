from typing import Optional, List
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ClassroomInfo(BaseModel):
    code: str
    building_name: str
    room_number: str
    floor: str
    room_name: str
    room_type: str
    professor_name: Optional[str]
    is_accessible: bool
    latitude: float
    longitude: float

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
    """수강신청 과목 정보 (course-mcp)"""
    code: str
    name: str
    professor: str
    credits: int
    time: str
    classroom: str
    classification: str

class CurriculumCourse(BaseModel):
    """교과과정 과목 정보 (curriculum-mcp)"""
    year: str
    code: str
    name: str
    credits: int
    semester: str
    prerequisites: List[str] = []

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
    courses: Optional[List[CourseInfo]] = None  # 수강신청 과목 (course-mcp)
    curriculum_courses: Optional[List[CurriculumCourse]] = None  # 교과과정 과목 (curriculum-mcp)
    show_courses: bool = False  # 추가