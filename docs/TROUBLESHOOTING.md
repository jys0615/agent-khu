# 문제 해결 가이드 🔧

Agent KHU 사용 중 발생할 수 있는 문제와 해결 방법을 정리했습니다.

---

## 📋 목차

- [리팩토링 엔지니어링 기록](#리팩토링-엔지니어링-기록)
- [설치 문제](#설치-문제)
- [API 및 인증 문제](#api-및-인증-문제)
- [데이터베이스 문제](#데이터베이스-문제)
- [MCP 서버 문제](#mcp-서버-문제)
- [Frontend 문제](#frontend-문제)
- [성능 문제](#성능-문제)

---

## 리팩토링 엔지니어링 기록

실제 운영 중 발견된 구조적 문제와 리팩토링 결정을 기록합니다.
각 항목은 **문제 → 원인 분석 → 해결 → 측정 결과** 형식으로 작성합니다.

---

### [Phase 1] MCP 콜드스타트 12초 문제 — 영구 세션 풀로 해결

**날짜**: 2026-04-24
**수정 파일**: `backend/app/mcp_client.py`, `backend/app/main.py`

#### 문제
모든 채팅 요청의 첫 번째 MCP tool 호출 시 12초 이상 대기 발생.
워밍업 핵(startup 시 dummy 호출 2회)으로 증상을 일시적으로 완화했으나,
워밍업이 실패하면 사용자 요청에서 콜드스타트가 그대로 노출됨.

```
[로그 예시 - Before]
INFO: MCP call: curriculum.get_requirements
DEBUG: stdio_client 프로세스 생성...
  → 12.3초 대기 (initialize timeout: 12s)
INFO: Tool 호출 완료
```

#### 원인 분석
기존 `call_tool()` 구조:
```
call_tool() 호출마다:
  async with stdio_client(params):       # subprocess spawn
    async with ClientSession(r, w):      # 세션 초기화
      await session.initialize()         # ← 최대 12초
      await session.call_tool(...)
  # 세션 종료 + subprocess 종료
```

MCP 스펙(`modelcontextprotocol.io`)은 서버를 **영구 프로세스**로 운영하고
클라이언트가 세션을 유지하는 방식을 의도함.
기존 구현은 요청마다 프로세스를 생성/종료하여 스펙을 위반하고 있었음.

#### 해결
`AsyncExitStack`으로 `stdio_client` + `ClientSession` 컨텍스트를
**FastAPI lifespan에 묶어** 앱 수명 동안 유지.

```python
class MCPServerSession:
    async def start(self) -> None:
        read, write = await self._exit_stack.enter_async_context(
            stdio_client(self.params)
        )
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await asyncio.wait_for(self._session.initialize(), timeout=15.0)

    async def call_tool(self, tool_name, arguments, timeout) -> Any:
        # 세션 없으면 lazy start, 실패 시 재연결 1회
        ...
        return await asyncio.wait_for(
            self._session.call_tool(tool_name, arguments), timeout=timeout
        )
```

재연결 경합 방지: `_reconnect_lock`으로 stop → start 구간만 직렬화.
기존 서버별 Lock(call 전체 직렬화)은 제거 — `ClientSession`이 JSON-RPC ID로 동시 요청을 처리함.

`main.py` lifespan 변경:
```python
# Before: lazy start 주석 + warmup 태스크 2개
log.info("MCP 서버는 첫 tool 호출 시 자동으로 시작됩니다.")
asyncio.create_task(_warmup())   # curriculum + classroom 미리 호출

# After: startup에서 모든 세션 동시 시작
await mcp_client.start_all()    # asyncio.gather() 6개 병렬 초기화
# shutdown
await mcp_client.stop_all()
```

#### 측정 결과

| 지표 | Before | After |
|---|---|---|
| 첫 번째 요청 레이턴시 | ~12s (콜드스타트) | **< 1s** (세션 이미 열림) |
| 요청당 subprocess spawn | 1회 | **0회** |
| `initialize()` 호출 빈도 | 요청마다 | **startup 1회** |
| warmup 코드 필요 여부 | 필요 (2개 서버) | **삭제** |
| startup 세션 초기화 방식 | N/A | `asyncio.gather()` 6개 병렬 |
| startup 소요 시간 증가 | 0s (lazy) | +약 5~15s (1회만 지불) |
| 실패 서버 복구 | 요청마다 에러 | lazy start 폴백 + 자동 재연결 |

> **포트폴리오 수치**: *"MCP 콜드스타트를 영구 세션 풀로 제거, 첫 요청 레이턴시 12s → 1s 미만 (>90% 감소)"*

#### 트러블슈팅 포인트
- `AsyncExitStack`을 `MCPServerSession` 인스턴스 변수로 유지하지 않으면
  `stop()` 후 `_exit_stack`이 이미 닫혀 재연결 시 `RuntimeError` 발생.
  → `stop()` 마지막에 `self._exit_stack = AsyncExitStack()` 으로 초기화.
- `start_all()` 중 일부 서버 실패 시 전체 startup을 막지 않도록
  `return_exceptions=True` 사용, 실패 서버만 lazy start로 대체.

---

### [Phase 2] 동기 Anthropic 클라이언트 이벤트 루프 블로킹 + 순차 Tool 실행

**날짜**: 2026-04-24
**수정 파일**: `backend/app/agent/complex_handler.py`

#### 문제 1 — 동기 클라이언트 이벤트 루프 블로킹

FastAPI는 단일 asyncio 이벤트 루프 위에서 모든 요청을 처리한다.
기존 코드는 동기 `Anthropic` 클라이언트를 사용했고, `messages.create()`가
HTTP 응답을 기다리는 동안 이벤트 루프 전체가 블로킹됐다.

```python
# Before — 이벤트 루프 블로킹
from anthropic import Anthropic
_client = Anthropic(api_key=...)

response = _client.messages.create(...)   # LLM 응답 3~10초 동안 블로킹
                                          # 이 시간 동안 다른 요청 처리 불가
```

동시 사용자가 2명이면 두 번째 요청은 첫 번째 LLM 응답이 끝날 때까지 대기.

#### 해결 1 — AsyncAnthropic 교체

```python
# After — 논블로킹
from anthropic import AsyncAnthropic
_client = AsyncAnthropic(api_key=...)

response = await _client.messages.create(...)  # 이벤트 루프 반환, 다른 요청 처리 가능
```

#### 문제 2 — 순차 Tool 실행 + 불필요한 sleep

Claude가 복수 tool을 한 번에 요청할 때(예: 학식 + 도서관 좌석 동시 조회)
기존 코드는 순차 실행 + 각 호출 사이 `asyncio.sleep(0.1)` 대기.

```python
# Before — 순차 실행
for tool in tool_calls:
    result = await process_tool_call(tool.name, ...)
    await asyncio.sleep(0.1)   # "MCP stdio 안정성 확보" 목적이었으나
                                # Phase 1 영구 세션 이후 불필요
# 2개 tool: tool1(2s) + 0.1s + tool2(2s) = ~4.1s
```

Phase 1에서 영구 세션 풀로 전환했기 때문에 stdio 경합 자체가 없어짐.
`asyncio.sleep(0.1)` 는 per-request subprocess 방식의 잔재였음.

#### 해결 2 — asyncio.gather() 병렬 실행

```python
# After — 병렬 실행
raw_results = await asyncio.gather(
    *[process_tool_call(tool.name, ...) for tool in tool_calls],
    return_exceptions=True,   # 하나 실패해도 나머지 결과 유지
)
# 2개 tool: max(tool1, tool2) ≈ 2s (가장 느린 것 기준)
```

`return_exceptions=True`: 하나의 tool 실패가 전체 응답을 막지 않도록.
실패한 tool은 `{"error": str(e)}`로 처리되고 나머지 결과는 정상 반환.

#### 측정 결과

| 지표 | Before | After |
|---|---|---|
| LLM 호출 중 이벤트 루프 | **블로킹** (3~10s) | 논블로킹 |
| 동시 요청 처리 가능 여부 | 불가 | **가능** |
| 복수 tool 실행 방식 | 순차 + sleep(0.1) | **asyncio.gather() 병렬** |
| 2개 tool 실행 시간 (예) | tool1 + 0.1 + tool2 ≈ 4.1s | max(tool1, tool2) ≈ **2s** |
| tool 실패 시 전체 응답 | 전파 실패 | **부분 성공 허용** |

> **포트폴리오 수치**: *"동기 Anthropic 클라이언트를 AsyncAnthropic으로 교체해 이벤트 루프 블로킹 제거, 멀티 tool 병렬화로 복수 도구 요청 응답 시간 ~50% 단축"*

#### 트러블슈팅 포인트
- `asyncio.sleep(0.1)` 제거가 안전한 이유: Phase 1에서 영구 세션을 도입해
  per-request subprocess spawn 경합이 없어졌기 때문. 세션 재사용 환경에서는
  동시 `call_tool()` 호출이 `ClientSession` 내부 JSON-RPC ID로 구분됨.
- `return_exceptions=True` 없이 gather를 쓰면 하나의 tool 타임아웃이
  전체 iteration을 ExceptionGroup으로 실패시킴. 부분 실패 허용이 필수.

### [Phase 3] 버그 수정 4건

**날짜**: 2026-04-24
**수정 파일**: `tool_executor.py`, `cache.py`, `observability.py`, `rag_agent.py`, `result_builder.py`

---

#### 3-1. `DEPT_TO_PROGRAM` dict 중복 (tool_executor.py)

**문제**: `_handle_get_requirements` (line ~406), `_handle_evaluate_progress` (line ~472), 캐시 키 생성부(line ~44)에 동일한 학과→프로그램 매핑 dict가 3군데 복붙.
학과 추가 시 3곳을 모두 수정해야 했고, 한 곳을 빠뜨리면 캐시 키와 실제 호출 결과가 불일치.

**해결**: 모듈 상단에 `_DEPT_TO_PROGRAM` 상수로 단일화, 전 3곳에서 참조.

```python
# Before — 3군데 각각 선언
dept_map = {"컴퓨터공학과": "KHU-CSE", "소프트웨어융합학과": "KHU-SW", ...}

# After — 모듈 상수 1개
_DEPT_TO_PROGRAM = {"컴퓨터공학과": "KHU-CSE", ..., "산업경영공학과": "KHU-IME"}
```

---

#### 3-2. `get_cache_info()` 메서드 누락 (cache.py)

**문제**: `main.py` `/health` 엔드포인트가 `cache_manager.get_cache_info()`를 호출하는데, `CacheManager`에는 `get_info()`만 존재 → `/health` 호출마다 `AttributeError` 500.

**증상**:
```
AttributeError: 'CacheManager' object has no attribute 'get_cache_info'
GET /health → 500 Internal Server Error
```

**해결**: `get_info()`를 위임하는 alias 추가.

```python
async def get_cache_info(self) -> dict:
    return await self.get_info()
```

---

#### 3-3. `datetime.utcnow()` DeprecationWarning (observability.py, rag_agent.py)

**문제**: Python 3.12부터 `datetime.utcnow()`가 deprecated. timezone-naive datetime을 반환해 Elasticsearch 타임스탬프에 timezone 정보가 없었음.

**해결**:
```python
# Before
from datetime import datetime
datetime.utcnow().isoformat()

# After
from datetime import datetime, timezone
datetime.now(timezone.utc).isoformat()
```

---

#### 3-4. `_append_meal_result`의 `list.get()` AttributeError (result_builder.py)

**문제**: `tool_executor.py`의 `_handle_get_today_meal`은 `{"meals": [meal_info]}` — **list** 반환.
`result_builder.py`의 `_append_meal_result`는 `meal.get("source_url")` 호출 → list에 `.get()` 없음 → `AttributeError`.

**재현 조건**: "오늘 학식 알려줘" 요청 시 원본 링크 추출 시도마다 발생. `except Exception: pass`로 묻혀 링크가 누락되었음.

**해결**:
```python
# Before
src = meal.get("source_url")   # meal이 list면 AttributeError

# After
first = meal[0] if isinstance(meal, list) and meal else None
item = first if first is not None else (meal if isinstance(meal, dict) else None)
if item:
    src = item.get("source_url") or item.get("menu_url")
```

**교훈**: `except Exception: pass` 패턴이 타입 버그를 숨겼음. 타입 검사 선행 후 `.get()` 호출.

### [Phase 4] Prometheus + Grafana 모니터링 추가

**날짜**: 2026-04-24
**신규 파일**: `backend/app/metrics.py`, `monitoring/prometheus.yml`, `monitoring/grafana/**`
**수정 파일**: `backend/app/main.py`, `tool_executor.py`, `agent_loop.py`, `docker-compose.yml`, `requirements.txt`

#### 구조

```
Grafana (3000) ← 시각화
    ↑ PromQL 쿼리
Prometheus (9090) ← 메트릭 저장
    ↑ 15초마다 scrape
Backend /metrics ← prometheus_client 노출
    ↑ 코드에서 직접 increment
metrics.py (Counter / Histogram / Gauge)
```

#### 수집 메트릭

| 메트릭 | 타입 | 레이블 | 의미 |
|---|---|---|---|
| `http_requests_total` | Counter | method, path, status | HTTP 요청 수 (자동) |
| `http_request_duration_seconds` | Histogram | method, path | HTTP 레이턴시 (자동) |
| `mcp_tool_calls_total` | Counter | tool_name, status | MCP 도구 호출 수 |
| `agent_routing_total` | Counter | route | RAG/LLM/Fallback 비율 |
| `agent_response_latency_seconds` | Histogram | route | Agent 응답 레이턴시 |
| `mcp_active_sessions` | Gauge | — | 현재 활성 MCP 세션 수 |

#### Grafana 대시보드 패널 4종
1. **라우팅 분포** — Pie chart: RAG vs LLM vs Fallback 비율
2. **MCP tool 호출 / 캐시 히트율** — Bar gauge: tool별 success/cache_hit/error
3. **레이턴시 P50/P95/P99** — Time series: histogram_quantile로 계산
4. **에러율 + 활성 세션** — Stat panel

#### 접속
```bash
docker-compose up -d
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3000  (로그인 불필요, anonymous viewer)
```

#### 트러블슈팅 포인트
- `prometheus-fastapi-instrumentator`는 FastAPI `app` 생성 직후, 라우터 등록 전에 `instrument(app).expose(app)`를 호출해야 `/metrics`가 정상 등록됨.
- Grafana provisioning 경로: `datasources/` + `dashboards/` 두 폴더가 모두 있어야 자동 로드. 한쪽만 있으면 대시보드가 보이지 않음.
- `mcp_active_sessions` Gauge는 startup에서 1회 set 후 세션 재연결 시 업데이트되지 않음 — 현재는 시작 시점 스냅샷. 필요 시 `MCPServerSession.start()` / `stop()`에 inc/dec 추가 가능.

---

## 설치 문제

### Python 버전 오류

**증상**:
```
Error: Python 3.9+ required
```

**해결**:
```bash
# Python 버전 확인
python3 --version

# Python 3.9+ 설치 (macOS)
brew install python@3.9

# Python 3.9+ 설치 (Ubuntu)
sudo apt install python3.9
```

---

### pip 설치 실패

**증상**:
```
ERROR: Could not install packages due to an OSError
```

**해결**:
```bash
# 1. pip 업그레이드
pip install --upgrade pip

# 2. 관리자 권한으로 설치
pip install --user -r requirements.txt

# 3. 가상환경에서 설치
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### Playwright 브라우저 설치 실패

**증상**:
```
playwright._impl._api_types.Error: Browser executable doesn't exist
```

**해결**:
```bash
# Playwright 재설치
pip uninstall playwright
pip install playwright

# 브라우저 설치
playwright install chromium

# 시스템 의존성 설치 (Linux)
playwright install-deps
```

---

## API 및 인증 문제

### Anthropic API 키 오류

**증상**:
```
Error: Anthropic API key is required
```

**해결**:
```bash
# 1. .env 파일 확인
cat backend/.env | grep ANTHROPIC_API_KEY

# 2. 키가 없으면 추가
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" >> backend/.env

# 3. 키 유효성 확인
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4-20250514","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```

**API 키 발급**:
1. https://console.anthropic.com/ 접속
2. 로그인/회원가입
3. API Keys 메뉴에서 생성

---

### JWT 토큰 만료

**증상**:
```json
{
  "detail": "Could not validate credentials"
}
```

**해결**:
```bash
# 1. 재로그인
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"student_id":"2019104488","password":"your_password"}'

# 2. 토큰 만료 시간 연장 (.env)
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24시간
```

---

### 401 Unauthorized

**증상**:
```
401 Unauthorized: Authentication required
```

**해결**:
```bash
# 1. Authorization Header 확인
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"test"}'

# 2. 토큰 형식 확인
# 올바른 형식: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## 데이터베이스 문제

### PostgreSQL 연결 실패

**증상**:
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**해결**:
```bash
# 1. PostgreSQL 실행 상태 확인
pg_isready

# 2. PostgreSQL 시작
# macOS
brew services start postgresql@15

# Ubuntu
sudo systemctl start postgresql

# Docker
docker-compose up -d postgres

# 3. 연결 정보 확인
echo $DATABASE_URL
# postgresql://username:password@host:port/database
```

---

### 데이터베이스 없음

**증상**:
```
sqlalchemy.exc.OperationalError: database "agent_khu" does not exist
```

**해결**:
```bash
# 1. psql 접속
psql -U postgres

# 2. 데이터베이스 생성
CREATE DATABASE agent_khu;
\q

# 3. 테이블 생성
cd backend
python init_db.py
```

---

### 테이블 없음

**증상**:
```
sqlalchemy.exc.ProgrammingError: relation "users" does not exist
```

**해결**:
```bash
# 테이블 재생성
cd backend
python init_db.py
```

---

### 마이그레이션 오류

**증상**:
```
alembic.util.exc.CommandError: Can't locate revision
```

**해결**:
```bash
# 1. 마이그레이션 초기화
alembic init alembic

# 2. 마이그레이션 생성
alembic revision --autogenerate -m "initial"

# 3. 마이그레이션 적용
alembic upgrade head
```

---

## 백엔드 컨테이너 시작 실패 (init_db.py)

**증상**:
```
ModuleNotFoundError: No module named 'parse_rooms'
```
컨테이너가 `Exited (1)` 상태로 바로 종료됨

**원인**: `init_db.py`가 `parse_rooms` 모듈을 현재 디렉토리에서 찾지만, 실제 파일은 `scripts/migrations/parse_rooms.py`에 있음

**해결**: 이미 수정됨 (`init_db.py`가 `scripts/migrations/` 경로를 sys.path에 추가). 동일 증상 재발 시:
```bash
# 파일 위치 확인
find backend/ -name "parse_rooms.py"

# init_db.py의 sys.path 확인
head -15 backend/init_db.py
```

---

## MCP 서버 문제

### MCP 서버 시작 실패

**증상**:
```
❌ MCP 'curriculum' 시작 실패: FileNotFoundError
```

**해결**:
```bash
# 1. MCP 디렉토리 확인
ls -la mcp-servers/

# 2. MCP_ROOT 환경변수 설정
export MCP_ROOT=/path/to/agent-khu/mcp-servers
echo "MCP_ROOT=/path/to/agent-khu/mcp-servers" >> backend/.env

# 3. 서버 파일 존재 확인
ls -la mcp-servers/curriculum-mcp/server.py
```

---

### MCP 서버 타임아웃

**증상**:
```
TimeoutError: MCP server initialization timeout
```

**해결**:
```bash
# 1. 타임아웃 시간 연장 (.env)
MCP_INIT_TIMEOUT=30
MCP_CALL_TIMEOUT=120

# 2. 수동으로 서버 테스트
cd mcp-servers/curriculum-mcp
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python server.py

# 3. 로그 확인
# 서버 내부에서 print()로 디버깅
```

---

### JSON-RPC 파싱 오류

**증상**:
```
json.decoder.JSONDecodeError: Expecting value
```

**해결**:
```python
# server.py에서 디버깅
def _readline():
    line = sys.stdin.readline()
    print(f"[DEBUG] Received: {line}", file=sys.stderr)  # stderr로 로그
    if not line:
        return None
    try:
        return json.loads(line.strip())
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parse error: {e}", file=sys.stderr)
        return None
```

---

### classroom MCP 첫 호출 실패 (TCPTransport closed)

**증상**:
```
Tool 실행 에러: unable to perform operation on <TCPTransport closed=True>; the handler is closed
```
"성무진 교수님 연구실" 등 강의실 검색 시 "시설 검색 시스템에 일시적인 문제" 응답

**원인**: classroom MCP 서버가 처음 시작할 때 DB 연결 초기화 시간이 길어 MCP 세션 타임아웃 발생 (콜드스타트 문제)

**해결**: 이미 수정됨 — 서버 시작 시 `main.py`에서 classroom MCP를 미리 워밍업함. 동일 증상 재발 시:
```bash
# 백엔드 로그에서 워밍업 확인
docker logs agent-khu-backend 2>&1 | grep "워밍업"
# 정상: "MCP 워밍업: classroom.search_classroom 완료"

# 워밍업 없으면 백엔드 재시작
docker restart agent-khu-backend
```

---

### 도서관 좌석 스케줄러 크래시

**증상**:
```
❌ 도서관 크롤링 에러: app.models.LibrarySeat() argument after ** must be a mapping, not str
```
백그라운드 도서관 좌석 자동 크롤링이 10분마다 실패

**원인**: 스크래퍼가 `{"seats": [...], "success": bool}` dict를 반환하는데, 스케줄러가 dict 자체를 리스트처럼 순회해 string 키가 `**` 언패킹에 들어감

**해결**: 이미 수정됨 — `scheduler.py`의 `sync_library_seats()`에서 `data.get("seats", [])` 로 추출. 단, KHU 도서관 사이트 SSL 인증서 문제(`ERR_CERT_COMMON_NAME_INVALID`)로 실시간 크롤링 자체는 외부 이슈:
```
⚠️ 도서관 좌석 업데이트 건너뜀: 좌석 현황을 불러오지 못했습니다.
```
이 메시지는 에러가 아닌 정상 처리 결과임 (사용자 직접 질의 시에는 별도 경로로 처리)

---

### 크롤링 실패

**증상**:
```
HTTPError: 404 Not Found
```

**해결**:
```bash
# 1. URL 확인
curl -I https://ce.khu.ac.kr/ce/user/contents/view.do?menuNo=1600054

# 2. 수동 크롤링 테스트
cd mcp-servers/curriculum-mcp
python scrapers/curriculum_scraper.py

# 3. 캐시 초기화
rm data/curriculum_data.json
rm data/cache.json
```

---

## Frontend 문제

### CORS 오류 (브라우저에 표시되지만, 실제 원인은 백엔드 500일 수 있음)

**증상**:
```
Access to fetch at 'http://localhost:8000' has been blocked by CORS policy
```

**해결**:
```bash
# 1. Backend .env 확인
cat backend/.env | grep CORS_ALLOW_ORIGINS

# 2. Frontend URL 추가
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:3000

# 3. Backend 재시작
cd backend
uvicorn app.main:app --reload
```

추가 점검:
- 백엔드 로그에서 `ResponseValidationError`가 있는지 확인 (스키마 불일치가 500을 유발 → CORS처럼 보임)
```bash
docker logs agent-khu-backend --tail 100
```
-

### 학식 링크 버튼이 열리지 않음

**원인**:
- 백엔드 `MealInfo` 스키마에 `source_url`, `menu_url` 필드가 없으면 직렬화 단계에서 필드가 제거됨
- 프론트엔드에서 `response.meals`를 메시지에 전달하지 않음

**해결**:
1. Backend: `backend/app/schemas.py`의 `MealInfo`에 `menu_url`, `source_url` 추가
2. Frontend: `frontend/src/components/ChatInterface.tsx`에서 `meals: response.meals` 추가
3. Frontend: `frontend/src/components/MealCard.tsx`에서 URL에 프로토콜이 없으면 `https://` 자동 보정

### 다크 모드가 부분적으로만 적용됨

**원인**:
- 페이지 루트 배경에 라이트 그라디언트가 남아있음
- 카드 외곽선(ring)이 라운딩을 덮어 어색한 모서리 표시

**해결**:
1. Chat 페이지 루트: 다크 모드일 때 `bg-slate-900` 고정 배경 적용 (파일: `frontend/src/pages/Chat.tsx`)
2. ChatInterface 컨테이너: `ring` 대신 `border`로 변경, `rounded-[24px]`로 곡률 개선 (파일: `frontend/src/components/ChatInterface.tsx`)
3. 전체 다크 테마 팔레트 재조정: `index.css`에 slate 계열 색상 적용

---

### API 연결 실패

**증상**:
```
Network Error: ERR_CONNECTION_REFUSED
```

**해결**:
```bash
# 1. Backend 실행 확인
curl http://localhost:8000/

# 2. Frontend .env 확인
cat frontend/.env | grep VITE_API_URL
# VITE_API_URL=http://localhost:8000

# 3. Frontend 재시작
cd frontend
npm run dev
```

---

### npm 설치 오류

**증상**:
```
npm ERR! code ELIFECYCLE
```

**해결**:
```bash
# 1. node_modules 삭제
rm -rf node_modules package-lock.json

# 2. npm 캐시 클리어
npm cache clean --force

# 3. 재설치
npm install

# 4. Node.js 버전 확인
node --version  # 18+ 필요
```

---

### Vite 환경변수 미적용

**증상**:
```
import.meta.env.VITE_API_URL is undefined
```

**해결**:
```bash
# 1. .env 파일 확인
cat frontend/.env

# 2. VITE_ 접두사 확인
# ❌ API_URL=http://localhost:8000
# ✅ VITE_API_URL=http://localhost:8000

# 3. 개발 서버 재시작 (필수!)
npm run dev
```

---

## 성능 문제

### 응답 속도 느림

**증상**:
채팅 응답이 10초 이상 걸림

**해결**:
```bash
# 1. MCP 서버 캐싱 확인
# curriculum-mcp는 자동 캐싱
ls -la mcp-servers/curriculum-mcp/data/

# 2. Database 인덱스 추가
# models.py에서 __table_args__ 확인

# 3. Claude API 호출 최적화
# agent.py에서 max_iterations 조정

# 4. 로그 레벨 조정
LOG_LEVEL=INFO  # DEBUG는 느림
```

---

### 메모리 부족

**증상**:
```
MemoryError: Unable to allocate memory
```

**해결**:
```bash
# 1. MCP 서버 재시작
# Lazy start 활용

# 2. Playwright 헤드리스 모드
# course-mcp에서 headless=True 확인

# 3. Docker 메모리 제한
docker-compose.yml:
  services:
    backend:
      deploy:
        resources:
          limits:
            memory: 2G
```

---

### Port 충돌

**증상**:
```
OSError: [Errno 48] Address already in use
```

**해결**:
```bash
# 1. 포트 사용 프로세스 확인
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# 2. 프로세스 종료
kill -9 <PID>

# 3. 다른 포트 사용
# Backend
PORT=8001 uvicorn app.main:app

# Frontend
npm run dev -- --port 5174
```

---

## Docker 문제

### Docker Compose 빌드 실패

**증상**:
```
ERROR: Service 'backend' failed to build
```

**해결**:
```bash
# 1. 캐시 없이 재빌드
docker-compose build --no-cache

# 2. 이미지 삭제 후 재빌드
docker-compose down --rmi all
docker-compose up -d

# 3. 로그 확인
docker-compose logs backend
```

---

### 컨테이너 시작 실패

**증상**:
```
ERROR: for backend  Cannot start service backend
```

**해결**:
```bash
# 1. 로그 확인
docker-compose logs backend

# 2. 환경변수 확인
docker-compose exec backend env | grep ANTHROPIC

# 3. 컨테이너 재시작
docker-compose restart backend
```

---

## 일반적인 디버깅 방법

### 로그 확인

```bash
# Backend 로그
cd backend
LOG_LEVEL=DEBUG uvicorn app.main:app --reload

# Docker 로그
docker-compose logs -f backend

# MCP 서버 로그 (stderr로 출력)
cd mcp-servers/curriculum-mcp
echo '...' | python server.py 2>&1 | tee debug.log
```

---

### 의존성 확인

```bash
# Python 패키지
pip list

# npm 패키지
npm list

# 버전 확인
python --version
node --version
psql --version
```

---

### 환경 초기화

```bash
# Backend
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
rm -rf node_modules package-lock.json
npm install

# Database
psql -U postgres -c "DROP DATABASE agent_khu;"
psql -U postgres -c "CREATE DATABASE agent_khu;"
python backend/init_db.py
```

---

## 도움 요청

문제가 해결되지 않으면:

1. **GitHub Issues**: https://github.com/jys0615/agent-khu/issues
2. **Discussions**: https://github.com/jys0615/agent-khu/discussions
3. **이메일**: jys0615234@gmail.com

**이슈 작성 시 포함할 정보**:
- 운영체제 및 버전
- Python/Node.js 버전
- 에러 메시지 전문
- 재현 단계
- 로그 파일