from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean
from datetime import datetime
from .database import Base


class Classroom(Base):
    """
    강의실 정보 모델
    """
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    building_name = Column(String(100), nullable=False)
    building_code = Column(String(10), nullable=False)
    room_number = Column(String(20), nullable=False)
    floor = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    naver_place_id = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<Classroom {self.code}: {self.building_name} {self.room_number}호>"


class Notice(Base):
    """
    공지사항 모델 (Instagram)
    """
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, index=True)
    instagram_id = Column(String(100), unique=True, index=True, nullable=False)
    shortcode = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    instagram_url = Column(String(500), nullable=False)
    image_url = Column(String(500), nullable=True)
    posted_at = Column(DateTime, nullable=False)
    crawled_at = Column(DateTime, default=datetime.utcnow)
    account_name = Column(String(100), default="khu_sw.union")
    likes = Column(Integer, nullable=True)
    comments = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Notice {self.instagram_id}: {self.title[:50]}>"