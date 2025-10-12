"""
데이터베이스 초기화 및 샘플 데이터 삽입
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal
from app import models
from parse_rooms import parse_all_rooms


def init_database():
    """데이터베이스 초기화"""
    print("🔧 데이터베이스 초기화 중...")
    
    # 모든 테이블 생성
    models.Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 기존 강의실 데이터 삭제
        db.query(models.Classroom).delete()
        db.commit()
        
        # 파싱된 공간 데이터 가져오기
        rooms = parse_all_rooms()
        
        print(f"📊 {len(rooms)}개 공간 데이터 삽입 중...")
        
        # 공간 데이터 삽입
        for room in rooms:
            classroom = models.Classroom(
                code=f"전{room['code']}" if not room['code'].startswith(('B', 'b')) else room['code'].upper(),
                building_name="전자정보대학관",
                room_number=room['code'],
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
        
        # 통계 출력
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
        
        # 공지사항 수 확인
        notice_count = db.query(models.Notice).count()
        print(f"📢 공지사항 {notice_count}개 존재")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    print("✨ 완료!")


if __name__ == "__main__":
    init_database()