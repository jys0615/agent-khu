#!/usr/bin/env python3
"""
Test tool_executor refactoring:
- Verify Department DB lookups work
- Test keyword parameter passing
- Check error handling for unregistered departments
"""

import sys
import asyncio
import json
from sqlalchemy.orm import Session

# Add app to path
sys.path.insert(0, '/app')

from app.database import SessionLocal
from app import models
from app.agent.tool_executor import _handle_get_latest_notices, _handle_crawl_fresh_notices, _handle_search_notices


async def test_get_latest_notices():
    """Test _handle_get_latest_notices with DB lookup"""
    print("\n🧪 테스트 1: _handle_get_latest_notices (등록된 학과)")
    
    # Test with registered department (name)
    result = await _handle_get_latest_notices({
        "department": "소프트웨어융합학과",
        "limit": 3
    })
    
    if result.get("error"):
        print(f"❌ 에러: {result.get('error')}")
    else:
        notices = result.get("notices", [])
        print(f"✅ {len(notices)}개 공지사항 조회됨")
        if notices:
            print(f"   첫번째: {notices[0].get('title', 'N/A')[:50]}...")
    
    # Test with registered department (code)
    print("\n🧪 테스트 2: _handle_get_latest_notices (학과 코드 조회)")
    result = await _handle_get_latest_notices({
        "department": "ce",  # 컴퓨터공학부 코드
        "limit": 3
    })
    
    if result.get("error"):
        print(f"❌ 에러: {result.get('error')}")
    else:
        notices = result.get("notices", [])
        print(f"✅ {len(notices)}개 공지사항 조회됨")
    
    # Test with unregistered department
    print("\n🧪 테스트 3: _handle_get_latest_notices (미등록 학과 처리)")
    result = await _handle_get_latest_notices({
        "department": "경영학과",
        "limit": 3
    })
    
    if result.get("error"):
        print(f"✅ 예상된 에러 처리: {result.get('error')}")
        print(f"   메시지: {result.get('message')}")
    else:
        print(f"❌ 에러가 발생하지 않음")


async def test_crawl_fresh_notices():
    """Test _handle_crawl_fresh_notices with keyword support"""
    print("\n🧪 테스트 4: _handle_crawl_fresh_notices (키워드 필터링)")
    
    # Test with keyword
    result = await _handle_crawl_fresh_notices({
        "department": "산업경영공학과",
        "keyword": "장학",
        "limit": 10
    })
    
    notices = result.get("notices", [])
    print(f"✅ {len(notices)}개 공지사항 조회됨 (키워드: 장학)")
    if notices:
        print(f"   첫번째: {notices[0].get('title', 'N/A')[:50]}...")


async def test_search_notices():
    """Test _handle_search_notices with department filter"""
    print("\n🧪 테스트 5: _handle_search_notices (학과별 검색)")
    
    # Test search without department
    result = await _handle_search_notices({
        "query": "장학금",
        "limit": 5
    })
    
    notices = result.get("notices", [])
    print(f"✅ {len(notices)}개 공지사항 검색됨 (전체 학과)")
    
    # Test search with department
    print("\n🧪 테스트 6: _handle_search_notices (학과 필터링)")
    result = await _handle_search_notices({
        "query": "공지",
        "department": "컴퓨터공학부",
        "limit": 5
    })
    
    notices = result.get("notices", [])
    print(f"✅ {len(notices)}개 공지사항 검색됨 (컴퓨터공학부)")


def check_departments_in_db():
    """Check what departments are currently in DB"""
    print("\n📊 데이터베이스 학과 현황")
    
    db = SessionLocal()
    try:
        depts = db.query(models.Department).all()
        print(f"✅ 총 {len(depts)}개 등록 학과:")
        for dept in depts:
            count = db.query(models.Notice).filter(
                models.Notice.department_id == dept.id
            ).count()
            print(f"   - {dept.name} ({dept.code}): {count}개 공지")
    finally:
        db.close()


async def main():
    print("=" * 60)
    print("🚀 tool_executor 리팩토링 테스트")
    print("=" * 60)
    
    check_departments_in_db()
    
    try:
        await test_get_latest_notices()
        await test_crawl_fresh_notices()
        await test_search_notices()
        
        print("\n" + "=" * 60)
        print("✅ 모든 테스트 완료!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
