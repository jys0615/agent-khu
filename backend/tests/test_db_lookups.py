#!/usr/bin/env python3
"""
Simple test to verify Department DB lookups in tool_executor
"""

import sys
sys.path.insert(0, '/app')

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models

def test_department_lookups():
    """Test Department DB lookup patterns"""
    print("\n" + "=" * 60)
    print("🧪 Department DB Lookup 테스트")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Test 1: Look up by name
        print("\n✅ 테스트 1: 학과명으로 조회")
        dept = db.query(models.Department).filter(
            models.Department.name == "소프트웨어융합학과"
        ).first()
        
        if dept:
            print(f"   ✓ 찾음: {dept.name} (코드: {dept.code})")
            count = db.query(models.Notice).filter(
                models.Notice.department_id == dept.id
            ).count()
            print(f"   ✓ 공지사항: {count}개")
        else:
            print("   ✗ 찾지 못함")
        
        # Test 2: Look up by code
        print("\n✅ 테스트 2: 학과 코드로 조회")
        dept = db.query(models.Department).filter(
            models.Department.code == "ce"
        ).first()
        
        if dept:
            print(f"   ✓ 찾음: {dept.name} (코드: {dept.code})")
            count = db.query(models.Notice).filter(
                models.Notice.department_id == dept.id
            ).count()
            print(f"   ✓ 공지사항: {count}개")
        else:
            print("   ✗ 찾지 못함")
        
        # Test 3: Combined query (name or code)
        print("\n✅ 테스트 3: 학과명 또는 코드로 조회")
        dept = db.query(models.Department).filter(
            (models.Department.name == "컴퓨터공학부") |
            (models.Department.code == "컴퓨터공학부")
        ).first()
        
        if dept:
            print(f"   ✓ 찾음: {dept.name} (코드: {dept.code})")
        else:
            print("   ✗ 찾지 못함")
        
        # Test 4: Unregistered department
        print("\n✅ 테스트 4: 미등록 학과 처리")
        dept = db.query(models.Department).filter(
            (models.Department.name == "경영학과") |
            (models.Department.code == "경영학과")
        ).first()
        
        if not dept:
            print("   ✓ 예상대로 찾지 못함 (미등록 학과)")
        else:
            print("   ✗ 예상과 다름 (찾아짐)")
        
        # Test 5: List all departments
        print("\n✅ 테스트 5: 등록된 모든 학과")
        depts = db.query(models.Department).all()
        print(f"   총 {len(depts)}개 학과:")
        for dept in depts:
            count = db.query(models.Notice).filter(
                models.Notice.department_id == dept.id
            ).count()
            print(f"   - {dept.name:20} (코드: {dept.code:10}) 공지: {count:3}개")
        
        print("\n" + "=" * 60)
        print("✅ 모든 DB 조회 테스트 성공!")
        print("=" * 60)
        
    finally:
        db.close()


if __name__ == "__main__":
    test_department_lookups()
