"""
검색 기능 직접 테스트
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app import crud

def test_search():
    db = SessionLocal()
    
    try:
        print("=== 검색 테스트 ===\n")
        
        # 1. 101 검색
        print("1. '101' 검색:")
        results = crud.search_classrooms(db, "101", 10)
        print(f"   결과 수: {len(results)}")
        for r in results:
            print(f"   - {r.code} ({r.room_number}): {r.room_name}")
        
        # 2. 전101 검색
        print("\n2. '전101' 검색:")
        results = crud.search_classrooms(db, "전101", 10)
        print(f"   결과 수: {len(results)}")
        for r in results:
            print(f"   - {r.code} ({r.room_number}): {r.room_name}")
        
        # 3. 조진성 검색
        print("\n3. '조진성' 검색:")
        results = crud.search_classrooms(db, "조진성", 10)
        print(f"   결과 수: {len(results)}")
        for r in results:
            print(f"   - {r.code} ({r.room_number}): {r.room_name} - 교수: {r.professor_name}")
        
        # 4. 강의실 검색
        print("\n4. '강의실' 검색:")
        results = crud.search_classrooms(db, "강의실", 10)
        print(f"   결과 수: {len(results)}")
        for r in results[:5]:
            print(f"   - {r.code} ({r.room_number}): {r.room_name}")
        
        # 5. B08 검색
        print("\n5. 'B08' 검색:")
        results = crud.search_classrooms(db, "B08", 10)
        print(f"   결과 수: {len(results)}")
        for r in results:
            print(f"   - {r.code} ({r.room_number}): {r.room_name}")
        
        # 6. get_classroom_by_code로 101 검색
        print("\n6. get_classroom_by_code('101'):")
        result = crud.get_classroom_by_code(db, "101")
        if result:
            print(f"   찾음: {result.code} ({result.room_number}): {result.room_name}")
        else:
            print("   못 찾음")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_search()