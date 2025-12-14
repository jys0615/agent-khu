#!/usr/bin/env python3
"""
Validate tool_executor.py refactoring by checking the code structure
- Verify SessionLocal import exists
- Verify Department DB lookup pattern in _handle_get_latest_notices
- Verify keyword parameter support in _handle_crawl_fresh_notices
- Verify department filter support in _handle_search_notices
"""

import re

def check_file(filepath):
    print("\n" + "=" * 70)
    print(f"🔍 {filepath} 검증")
    print("=" * 70)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = []
    
    # Check 1: SessionLocal import
    if "from ..database import SessionLocal" in content:
        checks.append(("✅", "SessionLocal import 존재"))
    else:
        checks.append(("❌", "SessionLocal import 누락"))
    
    # Check 2: Department DB lookup in _handle_get_latest_notices
    if "db.query(models.Department).filter(" in content and "_handle_get_latest_notices" in content:
        checks.append(("✅", "_handle_get_latest_notices에서 Department DB 조회"))
    else:
        checks.append(("❌", "_handle_get_latest_notices에서 Department DB 조회 누락"))
    
    # Check 3: Name or code lookup pattern
    if "(models.Department.name == department)" in content and "(models.Department.code == department)" in content:
        checks.append(("✅", "학과명 또는 코드로 조회하는 패턴"))
    else:
        checks.append(("❌", "학과명/코드 조회 패턴 누락"))
    
    # Check 4: Error handling for unregistered departments
    if 'if not dept:' in content and '미등록 학과' in content:
        checks.append(("✅", "미등록 학과 에러 처리"))
    else:
        checks.append(("❌", "미등록 학과 에러 처리 누락"))
    
    # Check 5: Keyword parameter in _handle_crawl_fresh_notices
    if 'keyword = tool_input.get("keyword")' in content:
        checks.append(("✅", "_handle_crawl_fresh_notices에서 keyword 파라미터"))
    else:
        checks.append(("❌", "keyword 파라미터 누락"))
    
    # Check 6: Department parameter in _handle_search_notices
    if '_handle_search_notices' in content and 'department = tool_input.get("department")' in content:
        checks.append(("✅", "_handle_search_notices에서 department 필터링"))
    else:
        checks.append(("❌", "department 필터링 누락"))
    
    # Check 7: No hardcoded dept_to_source mapping
    if 'dept_to_source = {' not in content:
        checks.append(("✅", "하드코딩된 dept_to_source 제거됨"))
    else:
        checks.append(("❌", "하드코딩된 dept_to_source 여전히 존재"))
    
    # Print results
    for icon, check in checks:
        print(f"{icon} {check}")
    
    # Summary
    passed = sum(1 for icon, _ in checks if icon == "✅")
    total = len(checks)
    
    print("\n" + "-" * 70)
    print(f"결과: {passed}/{total} 검사 통과")
    print("-" * 70)
    
    return passed == total


if __name__ == "__main__":
    filepath = "/app/app/agent/tool_executor.py"
    success = check_file(filepath)
    
    if success:
        print("\n🎉 모든 리팩토링 검증 성공!")
    else:
        print("\n⚠️ 일부 검사 실패")
    
    exit(0 if success else 1)
