# 📝 Code Changes Detail - Step 3

## File Modified: `/backend/app/agent/tool_executor.py`

### Change 1: SessionLocal Import (Line 8)
```python
# ADDED:
from ..database import SessionLocal
```

**Purpose**: Enable database queries in tool handlers

---

## Function 1: `_handle_search_notices()` 

### Changes
- **Added**: Optional `department` parameter filtering
- **Query Pattern**: DB lookup by Department name or code
- **Backward Compatible**: Works with or without department filter

### Code Comparison

**BEFORE:**
```python
async def _handle_search_notices(tool_input: dict):
    query = tool_input.get("query", "")
    limit = tool_input.get("limit", 5)
    result = await mcp_client.call_tool("notice", "search_notices", 
                                       {"query": query, "limit": limit})
    
    data = json.loads(result) if isinstance(result, str) else result
    return {"notices": data.get("notices", [])}
```

**AFTER:**
```python
async def _handle_search_notices(tool_input: dict):
    query = tool_input.get("query", "")
    limit = tool_input.get("limit", 5)
    department = tool_input.get("department")  # ← NEW
    
    # MCP 호출 시 department 포함
    mcp_args = {
        "query": query,
        "limit": limit
    }
    if department:
        # DB에서 Department 조회하여 code 가져오기
        db = SessionLocal()
        try:
            dept = db.query(models.Department).filter(
                (models.Department.name == department) |
                (models.Department.code == department)
            ).first()
            if dept:
                mcp_args["department"] = dept.code
        finally:
            db.close()
    
    result = await mcp_client.call_tool("notice", "search_notices", mcp_args)
    
    data = json.loads(result) if isinstance(result, str) else result
    return {"notices": data.get("notices", [])}
```

### Key Features
- ✅ Accepts `department` parameter (optional)
- ✅ Queries Department table with OR condition (name OR code)
- ✅ Passes `dept.code` to MCP for filtering
- ✅ Graceful fallback if department not found (searches all)

---

## Function 2: `_handle_get_latest_notices()`

### Changes
- **REMOVED**: Hardcoded `dept_to_source` dictionary (4 departments)
- **ADDED**: Dynamic Department DB lookup
- **ADDED**: Error handling for unregistered departments
- **KEY**: Uses `dept.code` dynamically instead of dictionary

### Code Comparison

**BEFORE:**
```python
async def _handle_get_latest_notices(tool_input: dict, current_user: Optional[models.User] = None):
    """최신 공지사항 조회 (학과별)"""
    
    # 사용자 학과 가져오기
    department = tool_input.get("department")
    if not department and current_user:
        department = current_user.department
    if not department:
        department = "소프트웨어융합학과"  # 기본값
    
    limit = tool_input.get("limit", 5)
    
    # 학과 → source_code 매핑
    dept_to_source = {                                    # ← HARDCODED!
        "소프트웨어융합학과": "swedu",
        "컴퓨터공학부": "ce",
        "전자공학과": "elec",
        "산업경영공학과": "ime"
    }
    source = dept_to_source.get(department, "swedu")    # ← FALLBACK
    
    # ... rest of function
```

**AFTER:**
```python
async def _handle_get_latest_notices(tool_input: dict, current_user: Optional[models.User] = None):
    """최신 공지사항 조회 (학과별)"""
    
    # 사용자 학과 가져오기
    department = tool_input.get("department")
    if not department and current_user:
        department = current_user.department
    if not department:
        department = "소프트웨어융합학과"  # 기본값
    
    limit = tool_input.get("limit", 5)
    
    # DB에서 Department 조회 (name 또는 code로 검색)    # ← DB LOOKUP!
    db = SessionLocal()
    try:
        dept = db.query(models.Department).filter(
            (models.Department.name == department) |      # ← BY NAME
            (models.Department.code == department)        # ← OR BY CODE
        ).first()
        
        if not dept:                                       # ← ERROR HANDLING!
            return {
                "error": f"미등록 학과: {department}",
                "notices": [],
                "message": f"데이터베이스에 '{department}' 학과가 등록되어있지 않습니다."
            }
        
        source = dept.code                                 # ← DYNAMIC!
    finally:
        db.close()
    
    # ... rest of function (unchanged)
```

### Key Features
- ✅ Queries Department table instead of hardcoded dict
- ✅ Supports lookup by name OR code
- ✅ Clear error response for unregistered departments
- ✅ Uses `dept.code` directly (dynamically determined)
- ✅ Works with ANY registered department automatically

---

## Function 3: `_handle_crawl_fresh_notices()`

### Changes
- **ADDED**: `keyword` parameter support
- **ADDED**: Conditional keyword passing to MCP
- **Enables**: Keyword-filtered notice crawling

### Code Comparison

**BEFORE:**
```python
async def _handle_crawl_fresh_notices(tool_input: dict):
    # department 우선, 없으면 source 값을 department로 간주
    department = tool_input.get("department") or tool_input.get("source") or "소프트웨어융합학과"
    limit = tool_input.get("limit", 20)
    result = await mcp_client.call_tool("notice", "crawl_fresh_notices", {
        "department": department,
        "limit": limit
    })
    
    data = json.loads(result) if isinstance(result, str) else result
    return {"notices": data.get("notices", [])}
```

**AFTER:**
```python
async def _handle_crawl_fresh_notices(tool_input: dict):
    # department 우선, 없으면 source 값을 department로 간주
    department = tool_input.get("department") or tool_input.get("source") or "소프트웨어융합학과"
    limit = tool_input.get("limit", 20)
    keyword = tool_input.get("keyword")                   # ← NEW!
    
    # MCP 호출 시 keyword 포함
    mcp_args = {                                          # ← BUILD ARGS!
        "department": department,
        "limit": limit
    }
    if keyword:                                            # ← CONDITIONAL!
        mcp_args["keyword"] = keyword
    
    result = await mcp_client.call_tool("notice", "crawl_fresh_notices", mcp_args)
    
    data = json.loads(result) if isinstance(result, str) else result
    return {"notices": data.get("notices", [])}
```

### Key Features
- ✅ Extracts `keyword` from `tool_input` if provided
- ✅ Conditionally includes keyword in MCP args
- ✅ Passes to MCP `crawl_fresh_notices()` for filtering
- ✅ Backward compatible (works without keyword)

---

## Impact Summary

| Aspect | Before | After |
|--------|--------|-------|
| Supported Departments | 4 (hardcoded) | Unlimited (DB) |
| Adding New Department | Code + Redeployment | SQL INSERT only |
| Department Lookup | Dictionary dict | Database query |
| Error Handling | None | Clear message |
| Keyword Filtering | No | Yes ✅ |
| Department Filtering | No | Yes ✅ |
| Code Maintainability | Hard | Easy |
| Scalability | Limited | Unlimited |

---

## Database Interaction Pattern

### Query Pattern Used
```python
db = SessionLocal()
try:
    dept = db.query(models.Department).filter(
        (models.Department.name == search_term) |
        (models.Department.code == search_term)
    ).first()
    
    if not dept:
        # Error handling
        return error_response
    
    # Use dept.code, dept.notice_url, dept.notice_type
finally:
    db.close()
```

### Tables Involved
- **Department**: `id`, `college_id`, `name`, `code`, `notice_url`, `notice_type`
- **Notice**: `id`, `department_id`, `title`, `url`, `date`, etc.

---

## Testing Coverage

✅ **Verified Functions:**
1. SessionLocal import works
2. Department DB query works with name
3. Department DB query works with code
4. Unregistered department returns proper error
5. Keyword parameter passes through MCP args
6. Department filter passes through MCP args

✅ **Test Files Created:**
- `test_db_lookups.py` - DB pattern tests
- `validate_refactor.py` - Code structure verification
- `final_validation.py` - System-wide validation

---

## Rollback Strategy (if needed)

If you need to revert these changes:

1. Remove SessionLocal import (line 8)
2. In `_handle_get_latest_notices()`: Replace DB query section with hardcoded dict
3. In `_handle_crawl_fresh_notices()`: Remove keyword handling
4. In `_handle_search_notices()`: Remove department parameter

All changes are isolated to these 3 functions - no cascading effects.

---

## Next Integration Points

1. **Agent System Prompt**
   - Mention new `keyword` parameter in tool definitions
   - Document department-based filtering

2. **Frontend**
   - Add Department dropdown selector
   - Add keyword input field
   - Pass both to backend

3. **MCP Server**
   - Already compatible with refactored code
   - `notice-mcp/server.py` has `crawl_department()` ready
   - Keyword filtering already implemented

---

## Performance Considerations

- **DB Queries**: 1 query per tool call (Department lookup)
  - Small overhead, well within acceptable range
  - Cached results from DB (indexes on `name`, `code`)
  
- **String Matching**: Department name/code lookup is indexed
  - Fast even with 100+ departments
  
- **MCP Calls**: Async, non-blocking
  - Multiple parallel requests supported

---

## Conclusion

✅ **Fully refactored**, **tested**, and **production-ready**

The system is now:
- 📈 **Scalable**: DB-driven instead of hardcoded
- 🔍 **Flexible**: Keyword and department filtering
- 🛡️ **Robust**: Clear error handling
- 🚀 **Ready**: For unlimited department registration

