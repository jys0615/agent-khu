"""
SQLAlchemy 모델 정의
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, Index
from sqlalchemy.orm import declarative_base
from datetime import datetime  # 이 줄 추가!

Base = declarative_base()


class Classroom(Base):
    """강의실 정보"""
    __tablename__ = "classrooms"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    building_name = Column(String(100), nullable=False)
    room_number = Column(String(20), nullable=False)
    floor = Column(String(10), nullable=False)
    room_name = Column(String(200), nullable=False)
    room_type = Column(String(50), nullable=False)
    professor_name = Column(String(100))
    is_accessible = Column(Boolean, default=True)
    keywords = Column(Text)
    latitude = Column(Float, default=37.24195)
    longitude = Column(Float, default=127.07945)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)


class Notice(Base):
    """공지사항"""
    __tablename__ = "notices"
    
    id = Column(Integer, primary_key=True, index=True)
    notice_id = Column(String(50), unique=True, nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    url = Column(String(500), nullable=False)
    date = Column(String(50), nullable=False)
    author = Column(String(100))
    views = Column(Integer, default=0)
    crawled_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)


class Meal(Base):
    """학식 메뉴"""
    __tablename__ = "meals"
    
    id = Column(Integer, primary_key=True, index=True)
    cafeteria = Column(String(100), nullable=False)
    meal_type = Column(String(20), nullable=False)
    date = Column(String(20), nullable=False, index=True)
    menu = Column(Text, nullable=False)
    price = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index('idx_cafeteria_date', 'cafeteria', 'date'),
    )


class LibrarySeat(Base):
    """도서관 좌석 현황"""
    __tablename__ = "library_seats"
    
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String(100), nullable=False)
    floor = Column(String(10))
    total_seats = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_location', 'location'),
    )


class ShuttleBus(Base):
    """셔틀버스 시간표"""
    __tablename__ = "shuttle_buses"
    
    id = Column(Integer, primary_key=True, index=True)
    route = Column(String(100), nullable=False)
    departure = Column(String(100), nullable=False)
    arrival = Column(String(100), nullable=False)
    weekday_times = Column(Text)
    weekend_times = Column(Text)
    semester_type = Column(String(20))
    note = Column(Text)
    
    __table_args__ = (
        Index('idx_route', 'route'),
    )


class Course(Base):
    """수강신청 강좌 정보"""
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
    semester = Column(String(10), nullable=False)
    course_code = Column(String(20), nullable=False)
    course_name = Column(String(200), nullable=False)
    professor = Column(String(100))
    department = Column(String(100))
    credits = Column(Integer)
    capacity = Column(Integer)
    class_time = Column(String(100))
    classroom = Column(String(50))
    classification = Column(String(50))
    language = Column(String(20))
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
    
    __table_args__ = (
        Index('idx_course_search', 'course_name', 'professor'),
        Index('idx_semester', 'year', 'semester'),
    )