"""
데이터베이스 초기화 및 샘플 데이터 삽입
"""
import sys
import os

_base = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _base)
sys.path.insert(0, os.path.join(_base, "scripts", "migrations"))

from app.database import engine, SessionLocal
from app import models
from parse_rooms import parse_all_rooms


# ---------- 학과 시드 데이터 ----------
COLLEGES_SEED = [
    {"name": "소프트웨어융합대학", "campus": "국제캠퍼스", "code": "swcon"},
    {"name": "공과대학",           "campus": "국제캠퍼스", "code": "eng"},
    {"name": "전자정보대학",       "campus": "국제캠퍼스", "code": "cse"},
    {"name": "경영대학",           "campus": "서울캠퍼스", "code": "business"},
    {"name": "정경대학",           "campus": "서울캠퍼스", "code": "polsci"},
    {"name": "이과대학",           "campus": "서울캠퍼스", "code": "science"},
]

DEPARTMENTS_SEED = [
    {
        "college_code": "swcon",
        "name": "소프트웨어융합학과",
        "code": "swedu",
        "notice_url": "http://swcon.khu.ac.kr/swcon/user/bbs/BMSR00040/list.do?menuNo=21300017",
        "notice_type": "standard",
    },
    {
        "college_code": "cse",
        "name": "컴퓨터공학부",
        "code": "ce",
        "notice_url": "https://ce.khu.ac.kr/ce/user/bbs/BMSR00040/list.do?menuNo=1600045",
        "notice_type": "standard",
    },
    {
        "college_code": "eng",
        "name": "산업경영공학과",
        "code": "ime",
        "notice_url": "https://ie.khu.ac.kr/ie/user/bbs/BMSR00040/list.do?menuNo=17400015",
        "notice_type": "standard",
    },
    {"college_code": "eng", "name": "기계공학과",   "code": "me",       "notice_url": None, "notice_type": "standard"},
    {"college_code": "eng", "name": "화학공학과",   "code": "chemeng",  "notice_url": None, "notice_type": "standard"},
    {"college_code": "eng", "name": "건축공학과",   "code": "archieng", "notice_url": None, "notice_type": "standard"},
    {"college_code": "cse", "name": "전자정보공학부","code": "elec",     "notice_url": None, "notice_type": "standard"},
]


def seed_departments(db) -> None:
    """단과대 / 학과 시드 데이터 삽입 (이미 있으면 notice_url만 갱신)."""
    # 단과대
    for cdata in COLLEGES_SEED:
        if not db.query(models.College).filter_by(code=cdata["code"]).first():
            db.add(models.College(**cdata))
    db.flush()

    # 학과
    for raw in DEPARTMENTS_SEED:
        college_code = raw["college_code"]
        dept_code    = raw["code"]
        dept_fields  = {k: v for k, v in raw.items() if k != "college_code"}

        existing = db.query(models.Department).filter_by(code=dept_code).first()
        if not existing:
            college = db.query(models.College).filter_by(code=college_code).first()
            if college:
                db.add(models.Department(college_id=college.id, **dept_fields))
        else:
            # notice_url이 업데이트됐을 수 있으므로 덮어쓰기
            if raw.get("notice_url"):
                existing.notice_url  = raw["notice_url"]
                existing.notice_type = raw.get("notice_type", "standard")

    db.commit()
    total = db.query(models.Department).count()
    print(f"✅ 학과 시드 완료 (총 {total}개)")


def normalize_code(code: str) -> str:
    """코드 정규화"""
    code_upper = code.upper()
    
    if code_upper.startswith('B'):
        return code_upper
    
    if code_upper.replace('-', '').replace('A', '').replace('B', '').replace('C', '').replace('D', '').replace('E', '').isdigit():
        return f"전{code}"
    
    return code


def init_database():
    """데이터베이스 초기화"""
    print("🔧 데이터베이스 초기화 중...")

    models.Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # 학과 시드 (항상 실행 — 데이터 없을 때 자동 삽입)
        try:
            seed_departments(db)
        except Exception as e:
            print(f"⚠️ 학과 시드 오류 (무시): {e}")

        existing = db.query(models.Classroom).count()

        # 이미 크롤링/데이터가 채워져 있으면 초기화 스킵
        if existing > 0 and not os.getenv("INIT_CLASSROOMS_FORCE"):
            print(f"✅ classrooms 테이블에 기존 데이터 {existing}건이 있어 초기화 건너뜀")
        else:
            rooms = parse_all_rooms()

            print(f"📊 {len(rooms)}개 공간 데이터 삽입 중...")

            # 건물명 변경
            BUILDING_NAME = "경희대학교 국제캠퍼스 전자정보대학관"

            for room in rooms:
                room_number = room['code']
                code = normalize_code(room['code'])

                classroom = models.Classroom(
                    code=code,
                    building_name=BUILDING_NAME,  # 변경된 건물명
                    room_number=room_number,
                    floor=room['floor'],
                    room_name=room['name'],
                    room_type=room['room_type'],
                    professor_name=room['professor_name'] if room['professor_name'] else None,
                    is_accessible=room['is_accessible'],
                    keywords=room['keywords'],
                    latitude=37.24195,
                    longitude=127.07945
                )
                db.add(classroom)

            db.commit()

            total = db.query(models.Classroom).count()
            classrooms = db.query(models.Classroom).filter(models.Classroom.room_type == 'classroom').count()
            professor_offices = db.query(models.Classroom).filter(models.Classroom.room_type == 'professor_office').count()
            labs = db.query(models.Classroom).filter(models.Classroom.room_type == 'lab').count()
            accessible = db.query(models.Classroom).filter(models.Classroom.is_accessible == True).count()

            print(f"✅ {total}개 공간 데이터 추가 완료!")
            print(f"   - 강의실: {classrooms}개")
            print(f"   - 교수 연구실: {professor_offices}개")
            print(f"   - 연구실/실험실: {labs}개")
            print(f"   - 학생 접근 가능: {accessible}개")

            print(f"\n📍 건물명: {BUILDING_NAME}")

            samples = db.query(models.Classroom).filter(
                models.Classroom.room_type == 'classroom'
            ).limit(3).all()

            print("\n샘플 데이터:")
            for sample in samples:
                print(f"   {sample.code} - {sample.building_name} {sample.room_number}호")

        # Notice 테이블 데이터 확인 (스키마 버전 호환성 체크)
        try:
            notice_count = db.query(models.Notice).count()
            print(f"\n 공지사항 {notice_count}개 존재")
        except Exception as e:
            print(f"\n 공지사항 조회 실패 (스키마 업데이트 중): {type(e).__name__}")

    except Exception as e:
        print(f" 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()
    
    print("✨ 완료!")


if __name__ == "__main__":
    init_database()