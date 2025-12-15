"""
데이터베이스 CRUD 작업
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from . import models, schemas
from typing import List, Optional
from datetime import datetime

def get_classroom_by_code(db: Session, code: str) -> Optional[models.Classroom]:
    """강의실 코드로 조회"""
    search_codes = [code, code.upper()]
    
    if code.startswith("전"):
        search_codes.append(code[1:])
    elif not code.startswith('B'):
        search_codes.append(f"전{code}")
    
    return db.query(models.Classroom).filter(
        or_(
            models.Classroom.code.in_(search_codes),
            models.Classroom.room_number.in_(search_codes)
        )
    ).first()


def get_classrooms(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    room_type: Optional[str] = None,
    floor: Optional[str] = None,
    accessible_only: bool = False
) -> List[models.Classroom]:
    """강의실 목록 조회"""
    query = db.query(models.Classroom)
    
    if room_type:
        query = query.filter(models.Classroom.room_type == room_type)
    if floor:
        query = query.filter(models.Classroom.floor == floor)
    if accessible_only:
        query = query.filter(models.Classroom.is_accessible == True)
    
    return query.offset(skip).limit(limit).all()


def search_classrooms(
    db: Session,
    query: str,
    limit: int = 10
) -> List[models.Classroom]:
    """강의실/공간 검색 (개선판)"""
    search_term = query.strip()
    
    # LIKE 패턴 (부분 일치)
    search_pattern = f"%{search_term}%"
    
    # 정확한 매칭 후보들
    search_codes = [search_term, search_term.upper(), search_term.lower()]
    
    # "전101" → ["전101", "101"]
    if search_term.startswith("전"):
        number_only = search_term[1:]
        search_codes.extend([number_only, number_only.upper()])
    
    # "101" → ["101", "전101"]
    elif search_term and search_term[0].isdigit():
        with_prefix = f"전{search_term}"
        search_codes.extend([with_prefix, with_prefix.upper()])
    
    # OR 조건으로 검색 (우선순위: 정확한 매칭 → LIKE 매칭)
    results = db.query(models.Classroom).filter(
        or_(
            # 1순위: 정확한 코드 매칭
            models.Classroom.code.in_(search_codes),
            models.Classroom.room_number.in_(search_codes),
            
            # 2순위: 부분 일치
            models.Classroom.code.ilike(search_pattern),
            models.Classroom.room_number.ilike(search_pattern),
            models.Classroom.room_name.ilike(search_pattern),
            models.Classroom.professor_name.ilike(search_pattern),
            models.Classroom.keywords.ilike(search_pattern)
        )
    ).limit(limit).all()
    
    return results


def get_classrooms_by_professor(db: Session, professor_name: str) -> List[models.Classroom]:
    """교수님 이름으로 연구실 검색"""
    return db.query(models.Classroom).filter(
        models.Classroom.professor_name.ilike(f"%{professor_name}%")
    ).all()


def get_latest_notices(
    db: Session,
    source: Optional[str] = None,
    limit: int = 10
) -> List[models.Notice]:
    """최신 공지사항 조회"""
    query = db.query(models.Notice).filter(models.Notice.is_active == True)
    
    if source:
        query = query.filter(models.Notice.source == source)
    
    return query.order_by(models.Notice.crawled_at.desc()).limit(limit).all()


def search_notices(
    db: Session,
    query: str,
    limit: int = 10
) -> List[models.Notice]:
    """공지사항 검색"""
    search_pattern = f"%{query}%"
    
    return db.query(models.Notice).filter(
        and_(
            models.Notice.is_active == True,
            or_(
                models.Notice.title.ilike(search_pattern),
                models.Notice.content.ilike(search_pattern)
            )
        )
    ).order_by(models.Notice.crawled_at.desc()).limit(limit).all()


def create_notice_from_mcp(db: Session, notice_data: dict) -> Optional[models.Notice]:
    """MCP에서 받은 공지사항 데이터 저장"""
    existing = db.query(models.Notice).filter(
        models.Notice.notice_id == notice_data.get("id")
    ).first()
    
    if existing:
        return None
    
    from datetime import datetime
    
    notice = models.Notice(
        notice_id=notice_data.get("id"),
        source=notice_data.get("source", "unknown"),
        title=notice_data.get("title", ""),
        content=notice_data.get("content", ""),
        url=notice_data.get("url", ""),
        date=notice_data.get("date", ""),
        author=notice_data.get("author"),
        views=notice_data.get("views", 0),
        crawled_at=datetime.now()
    )
    
    db.add(notice)
    db.commit()
    db.refresh(notice)
    
    return notice

def get_meals_by_date(db: Session, date: str, meal_type: str = None):
    """날짜별 학식 조회"""
    query = db.query(models.Meal).filter(models.Meal.date == date)
    
    if meal_type:
        query = query.filter(models.Meal.meal_type == meal_type)
    
    return query.all()


def create_meal(db: Session, meal_data: dict):
    """학식 메뉴 저장"""
    existing = db.query(models.Meal).filter(
        models.Meal.cafeteria == meal_data["cafeteria"],
        models.Meal.date == meal_data["date"],
        models.Meal.meal_type == meal_data["meal_type"]
    ).first()
    
    if existing:
        return None
    
    meal = models.Meal(**meal_data)
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal

def get_library_seats(db: Session):
    """도서관 좌석 현황 조회"""
    return db.query(models.LibrarySeat).all()


def update_library_seats(db: Session, seats_data: List[dict]):
    """도서관 좌석 현황 업데이트"""
    # 기존 데이터 삭제
    db.query(models.LibrarySeat).delete()
    
    # 새 데이터 삽입
    for seat in seats_data:
        seat_obj = models.LibrarySeat(**seat)
        db.add(seat_obj)
    
    db.commit()

def get_shuttle_schedule(db: Session, route: str = None):
    """셔틀버스 시간표 조회"""
    query = db.query(models.ShuttleBus)
    
    if route:
        query = query.filter(models.ShuttleBus.route.ilike(f"%{route}%"))
    
    return query.all()


def get_next_shuttle(db: Session, route: str, current_time: str, is_weekend: bool):
    """다음 버스 시간 조회"""
    import json
    from datetime import datetime
    
    shuttles = get_shuttle_schedule(db, route)
    
    if not shuttles:
        return None
    
    shuttle = shuttles[0]
    times = json.loads(shuttle.weekend_times if is_weekend else shuttle.weekday_times)
    
    # 현재 시간 이후 버스 찾기
    current = datetime.strptime(current_time, "%H:%M")
    
    for time_str in times:
        bus_time = datetime.strptime(time_str, "%H:%M")
        if bus_time > current:
            return {
                "route": shuttle.route,
                "departure": shuttle.departure,
                "arrival": shuttle.arrival,
                "next_time": time_str,
                "note": shuttle.note
            }
    
    return None

def search_courses(db: Session, keyword: str = None, professor: str = None, limit: int = 10):
    """강좌 검색"""
    query = db.query(models.Course)
    
    if keyword:
        query = query.filter(
            or_(
                models.Course.course_name.ilike(f"%{keyword}%"),
                models.Course.department.ilike(f"%{keyword}%")
            )
        )
    
    if professor:
        query = query.filter(models.Course.professor.ilike(f"%{professor}%"))
    
    return query.limit(limit).all()


def get_courses_by_time(db: Session, day: str, time_slot: str):
    """시간대별 강좌 검색"""
    search_pattern = f"%{day}%{time_slot}%"
    
    return db.query(models.Course).filter(
        models.Course.class_time.ilike(search_pattern)
    ).all()


def bulk_create_courses(db: Session, courses_data: List[dict]):
    """강좌 대량 저장"""
    for course in courses_data:
        existing = db.query(models.Course).filter(
            models.Course.course_code == course["course_code"],
            models.Course.year == course["year"],
            models.Course.semester == course["semester"]
        ).first()
        
        if not existing:
            course_obj = models.Course(**course)
            db.add(course_obj)
    
    db.commit()


import json
from passlib.context import CryptContext

# argon2 사용 (bcrypt 문제 회피)
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


# User CRUD
def get_user_by_student_id(db: Session, student_id: str) -> Optional[models.User]:
    """학번으로 사용자 조회"""
    return db.query(models.User).filter(models.User.student_id == student_id).first()


def create_user(db: Session, user_data: dict) -> models.User:
    """사용자 생성"""
    # 학번에서 입학년도 추출 (명시된 경우 우선)
    admission_year = user_data.get("admission_year") or int(user_data["student_id"][:4])
    
    # 비밀번호 해싱
    password_hash = hash_password(user_data["password"])
    
    user = models.User(
        student_id=user_data["student_id"],
        password_hash=password_hash,
        department=user_data["department"],
        campus=user_data["campus"],
        admission_year=admission_year,
        name=user_data.get("name"),
        is_transfer=user_data.get("is_transfer", False),
        transfer_year=user_data.get("transfer_year"),
        double_major=user_data.get("double_major"),
        minor=user_data.get("minor"),
        interests=json.dumps([]),
        preferences=json.dumps({})
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


def update_user_profile(db: Session, user_id: int, profile_data: dict) -> Optional[models.User]:
    """사용자 프로필 업데이트"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user:
        return None
    
    if "student_id" in profile_data and profile_data.get("student_id"):
        new_student_id = profile_data["student_id"]
        existing = get_user_by_student_id(db, new_student_id)
        if existing and existing.id != user_id:
            raise ValueError("이미 등록된 학번입니다")
        user.student_id = new_student_id
        # 학번 변경 시 입학년도 자동 업데이트 (명시값이 없을 때)
        if "admission_year" not in profile_data or profile_data.get("admission_year") is None:
            try:
                user.admission_year = int(new_student_id[:4])
            except Exception:
                pass

    if "admission_year" in profile_data and profile_data.get("admission_year") is not None:
        user.admission_year = profile_data["admission_year"]

    if "name" in profile_data:
        user.name = profile_data["name"]

    if "campus" in profile_data and profile_data.get("campus"):
        user.campus = profile_data["campus"]

    if "current_grade" in profile_data:
        user.current_grade = profile_data["current_grade"]
    
    if "interests" in profile_data:
        user.interests = json.dumps(profile_data["interests"])
    
    if "completed_credits" in profile_data:
        user.completed_credits = profile_data["completed_credits"]
    
    if "double_major" in profile_data:
        user.double_major = profile_data["double_major"]
    
    if "minor" in profile_data:
        user.minor = profile_data["minor"]
    
    if "is_transfer" in profile_data:
        user.is_transfer = profile_data["is_transfer"]
    
    if "transfer_year" in profile_data:
        user.transfer_year = profile_data["transfer_year"]
        # 편입생인 경우 학번 자동 계산 (편입년도 - 2)
        if profile_data["transfer_year"]:
            calculated_year = profile_data["transfer_year"] - 2
            # 학번의 앞 4자리만 업데이트 (예: 2019110635 → 1919110635 → 1919110635)
            if user.student_id and len(user.student_id) >= 4:
                remainder = user.student_id[4:]  # 뒤의 6자리
                user.student_id = str(calculated_year) + remainder
                user.admission_year = calculated_year
    
    if "preferences" in profile_data:
        user.preferences = json.dumps(profile_data["preferences"])
    
    user.updated_at = datetime.now()
    
    db.commit()
    db.refresh(user)
    
    return user


def update_last_login(db: Session, user_id: int):
    """마지막 로그인 시간 업데이트"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.last_login = datetime.now()
        db.commit()


# Curriculum CRUD
def get_curriculum(db: Session, department: str, admission_year: int) -> Optional[models.Curriculum]:
    """졸업요건 조회"""
    return db.query(models.Curriculum).filter(
        models.Curriculum.department == department,
        models.Curriculum.admission_year == admission_year
    ).first()


def create_curriculum(db: Session, curriculum_data: dict) -> models.Curriculum:
    """졸업요건 생성"""
    curriculum = models.Curriculum(
        department=curriculum_data["department"],
        admission_year=curriculum_data["admission_year"],
        requirements=json.dumps(curriculum_data["requirements"])
    )
    
    db.add(curriculum)
    db.commit()
    db.refresh(curriculum)
    
    return curriculum


def create_curriculum_from_mcp(db: Session, curriculum_data: dict, department: str = "컴퓨터공학부") -> Optional[models.Curriculum]:
    """
    MCP에서 받은 졸업요건 데이터 저장
    
    Args:
        curriculum_data: {
            "year": "2019",
            "single_major": {...},
            "double_major": {...},
            "minor": {...},
            "special_requirements": {...}
        }
        department: 학과명
    
    Returns:
        생성된 Curriculum 객체 또는 None (중복)
    """
    try:
        year = int(curriculum_data.get("year", 2025))
        
        # 중복 체크
        existing = db.query(models.Curriculum).filter(
            models.Curriculum.department == department,
            models.Curriculum.admission_year == year
        ).first()
        
        if existing:
            # 이미 존재하는 경우 업데이트
            print(f"🔄 {year}학년도 {department} 졸업요건 업데이트")
            existing.requirements = json.dumps(curriculum_data)
            db.commit()
            db.refresh(existing)
            return existing
        
        # 새로 생성
        print(f"✨ {year}학년도 {department} 졸업요건 생성")
        curriculum = models.Curriculum(
            department=department,
            admission_year=year,
            requirements=json.dumps(curriculum_data)
        )
        
        db.add(curriculum)
        db.commit()
        db.refresh(curriculum)
        
        return curriculum
    
    except Exception as e:
        print(f"❌ 졸업요건 저장 실패: {e}")
        db.rollback()
        return None


def get_curriculum_by_year_range(
    db: Session,
    department: str,
    start_year: int,
    end_year: int
) -> List[models.Curriculum]:
    """
    연도 범위로 졸업요건 조회
    """
    return db.query(models.Curriculum).filter(
        models.Curriculum.department == department,
        models.Curriculum.admission_year >= start_year,
        models.Curriculum.admission_year <= end_year
    ).all()