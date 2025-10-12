"""
Pydantic 스키마
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ClassroomBase(BaseModel):
    code: str
    building_name: str = "전자정보대학관"
    room_number: str
    floor: str
    room_name: str
    room_type: str
    professor_name: Optional[str] = None
    is_accessible: bool = True
    keywords: Optional[str] = None
    latitude: Optional[float] = 37.24195
    longitude: Optional[float] = 127.07945


class ClassroomCreate(ClassroomBase):
    pass


class Classroom(ClassroomBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NoticeBase(BaseModel):
    notice_id: str
    source: str
    title: str
    content: str
    url: str
    date: str
    author: Optional[str] = None
    views: Optional[int] = 0


class NoticeCreate(NoticeBase):
    pass


class Notice(NoticeBase):
    id: int
    crawled_at: datetime
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    message: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ChatResponse(BaseModel):
    message: str
    classroom: Optional[Classroom] = None
    map_link: Optional[str] = None
    show_map_button: bool = False
    notices: Optional[list[Notice]] = None
    show_notices: bool = False