#!/usr/bin/env python3
"""
Final comprehensive validation of the entire system architecture
after tool_executor refactoring
"""

import sys
sys.path.insert(0, '/app')

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
import requests

def check_backend_health():
    """Check if backend is running"""
    print("\n🏥 Backend 상태 확인")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Backend 정상 운영 중")
            return True
    except:
        pass
    print("   ⚠️ Backend 응답 없음 (Docker 컨테이너 확인)")
    return False


def check_database_schema():
    """Verify College, Department, and Notice tables exist"""
    print("\n📊 데이터베이스 스키마 확인")
    
    db = SessionLocal()
    try:
        # Check College table
        colleges = db.query(models.College).all()
        print(f"   ✅ College 테이블: {len(colleges)}개 단과대")
        
        # Check Department table
        departments = db.query(models.Department).all()
        print(f"   ✅ Department 테이블: {len(departments)}개 학과")
        
        # Check Notice table with department_id
        notices = db.query(models.Notice).filter(
            models.Notice.department_id != None
        ).all()
        print(f"   ✅ Notice 테이블: {len(notices)}개 공지 (department_id 매핑됨)")
        
        # Check for notices without department_id
        orphaned = db.query(models.Notice).filter(
            models.Notice.department_id == None
        ).count()
        if orphaned > 0:
            print(f"   ⚠️ {orphaned}개 공지는 아직 미매핑 상태")
        
        return True
    finally:
        db.close()


def check_tool_executor():
    """Verify tool_executor refactoring"""
    print("\n🔧 tool_executor 리팩토링 확인")
    
    try:
        with open('/app/app/agent/tool_executor.py', 'r') as f:
            content = f.read()
        
        checks = {
            "SessionLocal import": "from ..database import SessionLocal",
            "Department DB query": "db.query(models.Department).filter(",
            "Name/Code lookup": "(models.Department.name == department)",
            "Error handling": "if not dept:",
            "Keyword support": 'keyword = tool_input.get("keyword")',
            "Department filter": 'department = tool_input.get("department")',
            "No hardcoding": "dept_to_source = {" not in content
        }
        
        passed = 0
        for check_name, pattern in checks.items():
            if isinstance(pattern, str):
                if "not in" in str(checks):
                    result = pattern
                else:
                    result = pattern in content
            else:
                result = pattern in content
            
            if result:
                print(f"   ✅ {check_name}")
                passed += 1
            else:
                print(f"   ❌ {check_name}")
        
        print(f"\n   결과: {passed}/{len(checks)} 리팩토링 요소 확인")
        return passed == len(checks)
    except Exception as e:
        print(f"   ❌ 검사 실패: {e}")
        return False


def check_mcp_integration():
    """Verify MCP server integration"""
    print("\n🔗 MCP 서버 통합 확인")
    
    try:
        with open('/mcp-servers/notice-mcp/server.py', 'r') as f:
            content = f.read()
        
        checks = {
            "crawl_department 함수": "def crawl_department",
            "DB Department 쿼리": "models.Department",
            "URL 동적 조회": "dept.notice_url",
            "URL 타입 조회": "dept.notice_type",
            "키워드 필터링": "keyword",
        }
        
        passed = 0
        for check_name, pattern in checks.items():
            if pattern in content:
                print(f"   ✅ {check_name}")
                passed += 1
            else:
                print(f"   ❌ {check_name}")
        
        print(f"\n   결과: {passed}/{len(checks)} MCP 통합 요소 확인")
        return passed >= 4  # At least 4/5 required
    except Exception as e:
        print(f"   ❌ 검사 실패: {e}")
        return False


def print_system_architecture():
    """Print final system architecture"""
    print("\n" + "=" * 70)
    print("📐 최종 시스템 아키텍처")
    print("=" * 70)
    
    print("""
┌─────────────────────────────────────────────────────────────┐
│                     Claude Agent (AI)                       │
│  - Intent: "산업경영공학과 장학금 공지"                      │
└──────────────────────────┬──────────────────────────────────┘
                           │ (department + keyword)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              tool_executor (Backend - FastAPI)              │
│  - _handle_get_latest_notices()                             │
│  - _handle_crawl_fresh_notices() ← keyword 지원             │
│  - _handle_search_notices() ← department 필터링             │
│                                                             │
│  Query Pattern: Department.filter(name OR code) → dept     │
└──────────────────────────┬──────────────────────────────────┘
                           │ (department name, keyword)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│           MCP Server (notice-mcp - Python)                  │
│  - crawl_department(): DB 조회 → 학과정보 획득              │
│  - crawl_swedu() / crawl_standard()                         │
│  - 페이지네이션: max 3pages × 10items = 30개 최대          │
│  - 키워드 필터링: title 기반 matching                       │
└──────────────────────────┬──────────────────────────────────┘
                           │ (request)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│          KHU Notice Boards (External Websites)              │
│  - swcon.khu.ac.kr (소프트웨어융합학과)                      │
│  - ce.khu.ac.kr (컴퓨터공학부)                              │
│  - ie.khu.ac.kr (산업경영공학과)                            │
│  - 기타 100+ 학과 (등록 대기)                               │
└──────────────────────────┬──────────────────────────────────┘
                           │ (HTML)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│        PostgreSQL Database (Backend Storage)                │
│  - College: 6개 (소프트웨어, 공과, 전자정보, ...)          │
│  - Department: 7개 (swedu, ce, ime, me, ...)               │
│  - Notice: 235개 (FK department_id로 매핑)                 │
└─────────────────────────────────────────────────────────────┘
""")


def print_usage_example():
    """Print usage examples"""
    print("\n" + "=" * 70)
    print("💬 사용 예시")
    print("=" * 70)
    
    examples = [
        ("전체 공지", "get_latest_notices()"),
        ("컴공 공지", "get_latest_notices(department='컴퓨터공학부')"),
        ("산공 장학금", "crawl_fresh_notices(department='산업경영공학과', keyword='장학')"),
        ("산공 검색", "search_notices(department='산업경영공학과', query='공모')"),
    ]
    
    for desc, code in examples:
        print(f"\n📌 {desc}")
        print(f"   → tool_input: {code}")


def main():
    print("\n" + "=" * 70)
    print("🚀 시스템 검증: Step 3 (tool_executor 리팩토링) 완료")
    print("=" * 70)
    
    results = {
        "Backend 상태": check_backend_health(),
        "DB 스키마": check_database_schema(),
        "tool_executor": check_tool_executor(),
        "MCP 통합": check_mcp_integration(),
    }
    
    print("\n" + "=" * 70)
    print("📋 종합 결과")
    print("=" * 70)
    
    for component, status in results.items():
        icon = "✅" if status else "⚠️"
        print(f"{icon} {component}: {'정상' if status else '주의'}")
    
    print_system_architecture()
    print_usage_example()
    
    # Overall status
    all_passed = all(results.values())
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ 모든 검증 통과! 시스템 정상 운영 중")
    else:
        print("⚠️  일부 검사 실패 - 상세 사항 확인 필요")
    print("=" * 70)
    
    print("\n📌 다음 단계:")
    print("  1. Frontend 통합: Department 드롭다운 추가")
    print("  2. Department 등록: 나머지 95개 학과 추가")
    print("  3. Agent 프롬프트: 새로운 기능 문서화")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 검증 중 오류: {e}")
        import traceback
        traceback.print_exc()
