"""
데이터베이스 초기화 및 샘플 데이터 삽입
"""
from app.database import SessionLocal, engine, Base
from app.models import Classroom, Notice  # 🆕 Notice 추가

# 전자정보대학관 좌표
BUILDING_LAT = 37.2420
BUILDING_LON = 127.0794


def init_db():
    """
    데이터베이스 테이블 생성 및 샘플 데이터 삽입
    """
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # 기존 데이터 확인
    existing = db.query(Classroom).first()
    if existing:
        print("강의실 데이터가 이미 존재합니다.")
    else:
        # 샘플 강의실 데이터
        sample_classrooms = [
            # 1층
            {"code": "전101", "building_name": "전자정보대학관", "building_code": "전", 
             "room_number": "101", "floor": 1, "capacity": 40, 
             "description": "전자정보대학관 1층 101호 강의실", 
             "latitude": BUILDING_LAT, "longitude": BUILDING_LON},
            
            {"code": "전102", "building_name": "전자정보대학관", "building_code": "전", 
             "room_number": "102", "floor": 1, "capacity": 40,
             "description": "전자정보대학관 1층 102호 강의실",
             "latitude": BUILDING_LAT, "longitude": BUILDING_LON},
            
            {"code": "전103", "building_name": "전자정보대학관", "building_code": "전", 
             "room_number": "103", "floor": 1, "capacity": 50,
             "description": "전자정보대학관 1층 103호 강의실",
             "latitude": BUILDING_LAT, "longitude": BUILDING_LON},
            
            # 2층
            {"code": "전201", "building_name": "전자정보대학관", "building_code": "전", 
             "room_number": "201", "floor": 2, "capacity": 40,
             "description": "전자정보대학관 2층 201호 강의실",
             "latitude": BUILDING_LAT, "longitude": BUILDING_LON},
            
            {"code": "전202", "building_name": "전자정보대학관", "building_code": "전", 
             "room_number": "202", "floor": 2, "capacity": 40,
             "description": "전자정보대학관 2층 202호 강의실",
             "latitude": BUILDING_LAT, "longitude": BUILDING_LON},
            
            {"code": "전203", "building_name": "전자정보대학관", "building_code": "전", 
             "room_number": "203", "floor": 2, "capacity": 30,
             "description": "전자정보대학관 2층 203호 - 행정실",
             "latitude": BUILDING_LAT, "longitude": BUILDING_LON},
            
            {"code": "전204", "building_name": "전자정보대학관", "building_code": "전", 
             "room_number": "204", "floor": 2, "capacity": 40,
             "description": "전자정보대학관 2층 204호 강의실",
             "latitude": BUILDING_LAT, "longitude": BUILDING_LON},
            
            # 3층
            {"code": "전301", "building_name": "전자정보대학관", "building_code": "전", 
             "room_number": "301", "floor": 3, "capacity": 40,
             "description": "전자정보대학관 3층 301호 강의실",
             "latitude": BUILDING_LAT, "longitude": BUILDING_LON},
            
            {"code": "전302", "building_name": "전자정보대학관", "building_code": "전", 
             "room_number": "302", "floor": 3, "capacity": 40,
             "description": "전자정보대학관 3층 302호 강의실",
             "latitude": BUILDING_LAT, "longitude": BUILDING_LON},
            
            {"code": "전303", "building_name": "전자정보대학관", "building_code": "전", 
             "room_number": "303", "floor": 3, "capacity": 50,
             "description": "전자정보대학관 3층 303호 강의실",
             "latitude": BUILDING_LAT, "longitude": BUILDING_LON},
            
            # 4층
            {"code": "전401", "building_name": "전자정보대학관", "building_code": "전", 
             "room_number": "401", "floor": 4, "capacity": 40,
             "description": "전자정보대학관 4층 401호 강의실",
             "latitude": BUILDING_LAT, "longitude": BUILDING_LON},
            
            {"code": "전402", "building_name": "전자정보대학관", "building_code": "전", 
             "room_number": "402", "floor": 4, "capacity": 40,
             "description": "전자정보대학관 4층 402호 강의실",
             "latitude": BUILDING_LAT, "longitude": BUILDING_LON},
            
            {"code": "전403", "building_name": "전자정보대학관", "building_code": "전", 
             "room_number": "403", "floor": 4, "capacity": 50,
             "description": "전자정보대학관 4층 403호 강의실",
             "latitude": BUILDING_LAT, "longitude": BUILDING_LON},
        ]
        
        for classroom_data in sample_classrooms:
            classroom = Classroom(**classroom_data)
            db.add(classroom)
        
        db.commit()
        print(f"✅ {len(sample_classrooms)}개의 샘플 강의실 데이터가 추가되었습니다.")
    
    # Notice 테이블 확인
    notice_count = db.query(Notice).count()
    print(f"📢 공지사항 {notice_count}개 존재")
    
    db.close()


if __name__ == "__main__":
    print("🔧 데이터베이스 초기화 중...")
    init_db()
    print("✨ 완료!")