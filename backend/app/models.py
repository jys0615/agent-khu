"""
SQLAlchemy 모델 정의
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, Index, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime  # 이 줄 추가!

Base = declarative_base()


class College(Base):
    """단과대학"""
    __tablename__ = "colleges"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    campus = Column(String(20), nullable=False)  # 서울캠퍼스, 국제캠퍼스, 공통
    code = Column(String(20), unique=True)  # eng, sci, cse 등
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationship
    departments = relationship("Department", back_populates="college")


class Department(Base):
    """학과/학부"""
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=True)  # 융합전공 등은 null 가능
    name = Column(String(200), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # swedu, ime, ce 등
    
    # 공지사항 크롤링 정보
    notice_url = Column(String(500))  # 공지사항 게시판 URL
    notice_type = Column(String(20), default="standard")  # standard, custom 등
    
    # 계층 구조: 학부 → 학과
    parent_department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
    
    # Relationships
    college = relationship("College", back_populates="departments")
    notices = relationship("Notice", back_populates="department")
    parent = relationship("Department", remote_side=[id], backref="sub_departments")
    
    __table_args__ = (
        Index('idx_dept_name', 'name'),
        Index('idx_dept_code', 'code'),
    )


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
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    url = Column(String(500), nullable=False)
    date = Column(String(50), nullable=False)
    author = Column(String(100))
    views = Column(Integer, default=0)
    crawled_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)
    
    # Relationship
    department = relationship("Department", back_populates="notices")


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


class User(Base):
    """사용자 정보"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(20), unique=True, nullable=False, index=True)  # 학번
    password_hash = Column(String(255), nullable=False)  # bcrypt 해시
    
    # 기본 정보 (필수)
    department = Column(String(100), nullable=False)  # 학과
    campus = Column(String(20), nullable=False)  # "국제캠퍼스" or "서울캠퍼스"
    admission_year = Column(Integer, nullable=False)  # 입학년도 (학번에서 파싱)
    
    # 선택 정보
    name = Column(String(100))  # 이름 (선택)
    is_transfer = Column(Boolean, default=False)  # 편입생 여부
    transfer_year = Column(Integer)  # 편입년도 (편입생인 경우)
    current_grade = Column(Integer)  # 현재 학년 (1-4)
    double_major = Column(String(100))  # 다전공
    minor = Column(String(100))  # 부전공
    
    # JSON 필드
    interests = Column(Text)  # JSON: ["AI", "백엔드", "클라우드"]
    completed_credits = Column(Integer, default=0)  # 이수 학점
    preferences = Column(Text)  # JSON: 사용자 설정
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
    last_login = Column(DateTime)
    
    # 인덱스
    __table_args__ = (
        Index('idx_student_id', 'student_id'),
        Index('idx_department_year', 'department', 'admission_year'),
    )


class Curriculum(Base):
    """졸업요건 정보"""
    __tablename__ = "curriculums"
    
    id = Column(Integer, primary_key=True, index=True)
    department = Column(String(100), nullable=False)
    admission_year = Column(Integer, nullable=False)
    
    # JSON 필드: 졸업요건
    requirements = Column(Text, nullable=False)  # JSON 형식
    # {
    #   "total_credits": 130,
    #   "major_required": 60,
    #   "major_elective": 18,
    #   ...
    # }
    
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        Index('idx_curriculum', 'department', 'admission_year'),
    )