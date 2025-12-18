# Classroom MCP Search Fix

## Problem Summary
Professor office queries (e.g., "박상근 교수 연구실", "우정원 교수") were failing with MCP tool errors.

## Root Causes Identified

### 1. Missing Classroom Data
- Initial DB only had 314 rooms from static `parse_rooms.py` (단일 건물)
- Actual campus has 33 buildings with 6033 rooms (33×more data)
- Missing: 대부분의 건물 및 교수 연구실

### 2. Crawler Implementation Gap
- Crawler (`crawl_classrooms.py`) was built but never executed
- Scheduler job existed but never ran (60-day interval, first execution pending)
- Data remained stale from initial seed

### 3. Cache Poisoning
- Initial MCP calls had TCPTransport errors during subprocess startup
- Failed/empty results got cached in Redis
- Subsequent requests served cached error results
- **Key issue**: Cache never expired naturally, kept serving bad data

## Solution Applied

### Step 1: Manual Crawler Execution
```bash
docker-compose exec backend env PYTHONPATH=/app python /app/../mcp-servers/classroom-mcp/scrapers/crawl_classrooms.py
```
**Result**: 6033 rooms processed, 5329 inserted, 704 updated, 0 errors

### Step 2: Cache Flush
```bash
docker-compose exec redis redis-cli FLUSHALL
```
Cleared poisoned cache entries that were blocking correct results.

### Step 3: Code Improvements

#### A. [init_db.py](backend/init_db.py) - Preserve Crawled Data
```python
# Skip classroom init if data exists (unless INIT_CLASSROOMS_FORCE=1)
existing = db.query(models.Classroom).count()
if existing > 0 and not os.getenv("INIT_CLASSROOMS_FORCE"):
    print(f"✅ classrooms 테이블에 기존 데이터 {existing}건이 있어 초기화 건너뜀")
else:
    # ... 기존 parse_rooms 로직
```
**Benefit**: Container restarts won't delete crawler-populated data.

#### B. [agent_loop.py](backend/app/agent/agent_loop.py) - Sequential MCP Execution
```python
# Changed from asyncio.gather (parallel) to sequential execution
for tool in tool_calls:
    result = await process_tool_call(...)
    results.append(result)
    await asyncio.sleep(0.1)  # Brief delay between calls
```
**Benefit**: Reduces MCP subprocess concurrency issues, prevents TCPTransport race conditions.

#### C. [tool_executor.py](backend/app/agent/tool_executor.py) - Increased Timeout & Retries
```python
result = await mcp_client.call_tool("classroom", "search_classroom", 
                                     {"query": query}, 
                                     timeout=10.0,  # 5→10초
                                     retries=2)     # 1→2회
```
**Benefit**: Gives MCP subprocesses more time to initialize and respond.

#### D. [mcp_client.py](backend/app/mcp_client.py) - Better Error Reporting
```python
# Enhanced exception handling with ExceptionGroup unwrapping
if hasattr(e, 'exceptions'):
    inner_errors = [str(ex) for ex in e.exceptions[:3]]
    error_msg = f"{error_msg} | Inner: {', '.join(inner_errors)}"
```
**Benefit**: Clearer debugging when MCP stdio failures occur.

## Verification

### Test 1: Professor Office Search
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "박상근 교수님 연구실 어디야?"}' | jq '.classroom'
```
**Expected**:
```json
{
  "building_name": "우정원",
  "room_number": "7033",
  "floor": "7",
  "room_name": "박상근교수연구실",
  "professor_name": "박상근",
  "latitude": 37.245978317165,
  "longitude": 127.077065846729
}
```
✅ **PASS**

### Test 2: Building Search
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "우정원 교수님 연구실"}' | jq '.classroom.building_name, .classroom.room_number'
```
**Expected**:
```
"우정원"
"B107"
```
✅ **PASS**

### Test 3: Direct MCP Call
```python
from app.mcp_client import mcp_client
res = await mcp_client.call_tool("classroom", "search_classroom", {"query": "박상근"})
# Returns: {"found": True, "classrooms": [...], "count": 1}
```
✅ **PASS**

## Database State After Fix

```sql
SELECT count(*) FROM classrooms;
-- 6033 (was 314)

SELECT count(*) FROM classrooms WHERE professor_name IS NOT NULL;
-- 수백 개 (was ~30)

SELECT * FROM classrooms WHERE professor_name LIKE '%박상근%';
-- 우정원 | 7033 | 박상근교수연구실 | 박상근
```

## Long-term Prevention

### 1. Scheduled Crawler Runs
Scheduler job active (60-day interval):
```python
# backend/app/scheduler.py
scheduler.add_job(
    sync_classrooms,
    IntervalTrigger(days=60),
    id="sync_classrooms",
    name="Classroom crawler (every 60 days)"
)
```

### 2. Cache Expiration Policy
Current TTLs ([tools_definition.py](backend/app/agent/tools_definition.py)):
```python
CACHE_TTL = {
    "search_classroom": 86400,  # 24시간
    # ...
}
```
**Recommendation**: Consider shorter TTL (e.g., 3600s/1h) during development.

### 3. Health Check Endpoint
**TODO**: Add `/health/mcp` endpoint to verify MCP servers are responding:
```python
@router.get("/health/mcp")
async def mcp_health():
    results = {}
    for server in ["classroom", "notice", "meal"]:
        try:
            await mcp_client.call_tool(server, "list_tools", {}, timeout=2.0)
            results[server] = "ok"
        except:
            results[server] = "error"
    return results
```

### 4. Cache Management UI
**TODO**: Admin interface to:
- View cached keys
- Clear specific cache entries
- Monitor cache hit/miss rates

## Rollback Instructions

If issues persist:

1. **Clear all cache**:
   ```bash
   docker-compose exec redis redis-cli FLUSHALL
   ```

2. **Revert to parallel execution** (if sequential causes delays):
   ```python
   # agent_loop.py
   results = await asyncio.gather(*[process_tool_call(...) for tool in tool_calls])
   ```

3. **Force classroom re-initialization**:
   ```bash
   docker-compose exec backend env INIT_CLASSROOMS_FORCE=1 python init_db.py
   ```

## Related Files Changed
- [backend/init_db.py](backend/init_db.py) - Skip re-init if data exists
- [backend/app/agent/agent_loop.py](backend/app/agent/agent_loop.py) - Sequential execution
- [backend/app/agent/tool_executor.py](backend/app/agent/tool_executor.py) - Timeout & retries
- [backend/app/mcp_client.py](backend/app/mcp_client.py) - Error handling
- [mcp-servers/classroom-mcp/scrapers/crawl_classrooms.py](mcp-servers/classroom-mcp/scrapers/crawl_classrooms.py) - Executed manually

## Monitoring

Watch for these in logs:
- `💾 Cache HIT/MISS: search_classroom` - Cache performance
- `❌ MCP Tool 호출 실패` - MCP subprocess errors
- `🔧 [MCP] stdio_client 연결됨` - MCP initialization (debug mode)

## Status
✅ **RESOLVED** - Professor office searches now working correctly with full campus data.
