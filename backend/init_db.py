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
            print(f"\n📢 공지사항 {notice_count}개 존재")
        except Exception as e:
            print(f"\n⚠️ 공지사항 조회 실패 (스키마 업데이트 중): {type(e).__name__}")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()
    
    print("✨ 완료!")


if __name__ == "__main__":
    init_database()