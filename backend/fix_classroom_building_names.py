#!/usr/bin/env python3
"""
강의실 DB에서 건물명의 줄바꿈/탭 문자를 정규화하는 마이그레이션 스크립트

문제: 건물명에 줄바꿈이 포함되어 있음
예시: "경희대학교 국제캠퍼스 \n전자정보대학관" → "경희대학교 국제캠퍼스 전자정보대학관"

실행: python fix_classroom_building_names.py
"""
import re
import sqlite3
from pathlib import Path

# SQLite DB 경로
DB_PATH = Path(__file__).resolve().parent / "test_bench.sqlite3"

def normalize_building_name(name: str) -> str:
    """건물명 정규화: 줄바꿈, 탭, 여러 공백을 단일 공백으로 변환"""
    if not name:
        return name
    
    # 줄바꿈, 탭 제거 및 여러 공백을 단일 공백으로
    normalized = re.sub(r'[\r\n\t]+', ' ', name)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


def main():
    if not DB_PATH.exists():
        print(f"❌ DB 파일 없음: {DB_PATH}")
        return 1
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        print(f"🔍 건물명 정규화 시작... (DB: {DB_PATH})")
        
        # 모든 강의실 조회
        cursor.execute("SELECT id, building_name FROM classrooms")
        classrooms = cursor.fetchall()
        print(f"📊 총 {len(classrooms)}개 강의실 조사")
        
        updated_count = 0
        
        for classroom_id, original_name in classrooms:
            normalized_name = normalize_building_name(original_name)
            
            # 변경이 필요한 경우만 업데이트
            if original_name != normalized_name:
                print(f"✏️  ID {classroom_id}: '{original_name}' → '{normalized_name}'")
                cursor.execute(
                    "UPDATE classrooms SET building_name = ? WHERE id = ?",
                    (normalized_name, classroom_id)
                )
                updated_count += 1
        
        conn.commit()
        
        if updated_count > 0:
            print(f"\n✅ {updated_count}개 강의실 건물명 정규화 완료")
        else:
            print("\n✅ 정규화 필요한 건물명이 없습니다")
        
        # 최종 결과 확인
        print("\n📋 건물명 현황:")
        cursor.execute("""
            SELECT building_name, COUNT(*) as count 
            FROM classrooms 
            GROUP BY building_name 
            ORDER BY count DESC
        """)
        
        for building_name, count in cursor.fetchall():
            print(f"  - {building_name}: {count}개 강의실")
        
        conn.close()
        return 0
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
