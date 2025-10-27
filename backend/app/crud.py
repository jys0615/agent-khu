"""
데이터베이스 CRUD 작업
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from . import models, schemas
from typing import List, Optional


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
    """강의실/공간 검색"""
    search_term = query.strip()
    search_pattern = f"%{search_term}%"
    
    search_codes = [search_term, search_term.upper()]
    
    if search_term.startswith("전"):
        search_codes.append(search_term[1:])
    elif search_term and not search_term.startswith('B') and search_term[0].isdigit():
        search_codes.append(f"전{search_term}")
    
    return db.query(models.Classroom).filter(
        or_(
            models.Classroom.code.in_(search_codes),
            models.Classroom.room_number.in_(search_codes),
            models.Classroom.code.ilike(search_pattern),
            models.Classroom.room_number.ilike(search_pattern),
            models.Classroom.room_name.ilike(search_pattern),
            models.Classroom.professor_name.ilike(search_pattern),
            models.Classroom.keywords.ilike(search_pattern)
        )
    ).limit(limit).all()


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
    
    from datetime import datetime  # 추가
    
    notice = models.Notice(
        notice_id=notice_data.get("id"),
        source=notice_data.get("source", "unknown"),
        title=notice_data.get("title", ""),
        content=notice_data.get("content", ""),
        url=notice_data.get("url", ""),
        date=notice_data.get("date", ""),
        author=notice_data.get("author"),
        views=notice_data.get("views", 0),
        crawled_at=datetime.now()  # 추가: 명시적으로 현재 시간 설정
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
    
    return None  # 막차 지남

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
    # "월수" + "3-4교시" 조합
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