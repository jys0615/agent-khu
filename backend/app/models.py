"""
데이터베이스 모델
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime
from sqlalchemy.sql import func
from .database import Base


class Classroom(Base):
    """강의실 및 공간 정보"""
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True)  # 전101, B08, 301
    building_name = Column(String(100), default="전자정보대학관")
    room_number = Column(String(20))  # 101, B08, 301
    floor = Column(String(10))  # "B", "1", "2", "3", "4"
    room_name = Column(String(200))  # 강의실, 조진성교수연구실 등
    room_type = Column(String(50))  # classroom, professor_office, lab 등
    professor_name = Column(String(100))  # 교수님 이름 (있는 경우)
    
    # 접근성
    is_accessible = Column(Boolean, default=True)  # 학생 접근 가능 여부
    
    # 검색용
    keywords = Column(Text)  # 쉼표로 구분된 키워드
    
    # 위치 정보 (기본값: 전자정보대학관)
    latitude = Column(Float, default=37.24195)
    longitude = Column(Float, default=127.07945)
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Notice(Base):
    """공지사항"""
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, index=True)
    notice_id = Column(String(50), unique=True, index=True)
    source = Column(String(50), index=True)  # swedu, department, schedule
    title = Column(String(500))
    content = Column(Text)
    url = Column(String(500))
    date = Column(String(50))
    author = Column(String(100))
    views = Column(Integer, default=0)
    crawled_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)