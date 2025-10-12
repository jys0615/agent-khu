from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# 기존 Classroom 스키마들...
class ClassroomBase(BaseModel):
    code: str = Field(..., description="강의실 코드 (예: 전101)")
    building_name: str = Field(..., description="건물명")
    building_code: str = Field(..., description="건물 코드")
    room_number: str = Field(..., description="호실")
    floor: int = Field(..., description="층수")
    capacity: Optional[int] = Field(None, description="수용 인원")
    description: Optional[str] = Field(None, description="설명")
    latitude: Optional[float] = Field(None, description="위도")
    longitude: Optional[float] = Field(None, description="경도")
    naver_place_id: Optional[str] = Field(None, description="네이버 장소 ID")


class ClassroomCreate(ClassroomBase):
    pass


class Classroom(ClassroomBase):
    id: int

    class Config:
        from_attributes = True


# 🆕 Notice 스키마들
class NoticeBase(BaseModel):
    instagram_id: str = Field(..., description="Instagram 게시물 ID")
    shortcode: str = Field(..., description="Instagram shortcode")
    title: str = Field(..., description="공지사항 제목")
    content: str = Field(..., description="공지사항 내용")
    instagram_url: str = Field(..., description="Instagram URL")
    image_url: Optional[str] = Field(None, description="이미지 URL")
    posted_at: datetime = Field(..., description="게시 날짜")
    account_name: str = Field(default="khu_sw.union", description="계정명")
    likes: Optional[int] = Field(None, description="좋아요 수")
    comments: Optional[int] = Field(None, description="댓글 수")


class NoticeCreate(NoticeBase):
    pass


class Notice(NoticeBase):
    id: int
    crawled_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# Chat 관련 스키마
class ChatRequest(BaseModel):
    message: str = Field(..., description="사용자 메시지")
    user_latitude: Optional[float] = Field(None, description="사용자 현재 위도")
    user_longitude: Optional[float] = Field(None, description="사용자 현재 경도")


class ChatResponse(BaseModel):
    message: str = Field(..., description="AI 응답 메시지")
    classroom_info: Optional[Classroom] = Field(None, description="강의실 정보")
    map_link: Optional[str] = Field(None, description="네이버 지도 링크")
    show_map_button: bool = Field(False, description="지도 버튼 표시 여부")
    notices: Optional[list[Notice]] = Field(None, description="공지사항 목록")  # 🆕
    show_notices: bool = Field(False, description="공지사항 표시 여부")  # 🆕