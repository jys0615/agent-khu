# API 문서 업데이트 (2025-12) 📡

Agent KHU Backend REST API의 새로운 엔드포인트 및 변경사항을 설명합니다.

---

## 🆕 새로운 엔드포인트

### 캐시 관리

#### 캐시 정보 조회

**GET** `/api/cache/info`

Redis 캐시 상태 및 통계를 조회합니다.

**Headers**
```
Authorization: Bearer {access_token}
```

**Response** `200 OK`
```json
{
  "connected": true,
  "version": "7.2.0",
  "used_memory_human": "2.5M",
  "total_keys": 142
}
```

---

#### 캐시 삭제 (패턴)

**DELETE** `/api/cache/pattern`

특정 패턴의 캐시를 삭제합니다.

**Headers**
```
Authorization: Bearer {access_token}
```

**Request Body**
```json
{
  "pattern": "search_notices:*"
}
```

**Response** `200 OK`
```json
{
  "deleted": 15,
  "pattern": "search_notices:*"
}
```

---

#### 전체 캐시 삭제

**DELETE** `/api/cache/clear`

모든 캐시를 삭제합니다. (관리자 전용, 주의!)

**Headers**
```
Authorization: Bearer {access_token}
```

**Response** `200 OK`
```json
{
  "success": true,
  "message": "모든 캐시가 삭제되었습니다"
}
```

---

### 교과과정 (Curriculum)

#### 교과과정 검색

**GET** `/api/curriculum/search`

교과과정 과목을 검색합니다.

**Query Parameters**
- `query` (string, required): 검색어 (과목명 또는 과목코드)
- `year` (string, optional): 학년도 (기본값: "latest")

**Example**
```
GET /api/curriculum/search?query=자료구조&year=2025
```

**Response** `200 OK`
```json
{
  "year": "2025",
  "courses": [
    {
      "code": "CSE204",
      "name": "자료구조",
      "credits": 3,
      "group": "전공 필수",
      "semesters": ["1", "2"]
    }
  ],
  "count": 1,
  "found": true
}
```

---

#### 졸업요건 조회

**GET** `/api/curriculum/requirements`

사용자의 졸업요건을 조회합니다.

**Headers**
```
Authorization: Bearer {access_token}
```

**Query Parameters**
- `program` (string, optional): 전공 코드 (예: KHU-CSE, 미제공 시 사용자 학과)
- `year` (string, optional): 입학년도 (미제공 시 사용자 입학년도)

**Example**
```
GET /api/curriculum/requirements?program=KHU-CSE&year=2019
```

**Response** `200 OK`
```json
{
  "program": "KHU-CSE",
  "program_name": "컴퓨터공학전공",
  "year": "2019",
  "total_credits": 130,
  "major_credits": 66,
  "groups": [
    {
      "key": "major_basic",
      "name": "전공기초",
      "min_credits": 12,
      "courses": ["CSE101", "CSE102"]
    },
    {
      "key": "major_required",
      "name": "전공필수",
      "min_credits": 18,
      "courses": ["CSE204", "CSE206", ...]
    },
    {
      "key": "major_elective",
      "name": "전공선택",
      "min_credits": 36,
      "courses": []
    }
  ],
  "found": true
}
```

---

#### 전공 프로그램 목록

**GET** `/api/curriculum/programs`

전공 프로그램 목록을 조회합니다.

**Query Parameters**
- `year` (string, optional): 학년도 (기본값: "latest")

**Example**
```
GET /api/curriculum/programs?year=2025
```

**Response** `200 OK`
```json
{
  "year": "2025",
  "programs": [
    {
      "code": "KHU-CSE",
      "name": "컴퓨터공학전공",
      "total_credits": 130
    }
  ],
  "found": true
}
```

---

## 📝 변경된 엔드포인트

### 채팅

#### 메시지 전송 (업데이트)

**POST** `/api/chat`

Claude AI와 대화합니다. Hybrid LLM/SLM 아키텍처 적용.

**Headers**
```
Authorization: Bearer {access_token}
```

**Request Body**
```json
{
  "message": "자료구조는 몇 학점이야?",
  "user_latitude": 37.5665,
  "user_longitude": 127.0000,
  "library_username": "2019104488",  // (선택) 도서관 좌석 조회 시
  "library_password": "password"     // (선택) 도서관 좌석 조회 시
}
```

**Response** `200 OK`
```json
{
  "message": "자료구조는 3학점 전공 필수 과목입니다.",
  "curriculum_courses": [
    {
      "code": "CSE204",
      "name": "자료구조",
      "credits": 3,
      "group": "전공 필수"
    }
  ],
  "show_courses": true,
  "requirements": null,
  "show_requirements": false,
  "evaluation": null,
  "show_evaluation": false,
  "notices": null,
  "show_notices": false,
  "meals": null,
  "show_meals": false,
  "library_seats": null,
  "show_library_seats": false,
  "needs_library_login": false
}
```

**Response Fields (업데이트)**
- `message` (string): AI 응답 텍스트
- `curriculum_courses` (array|null): 교과과정 과목 목록
- `requirements` (object|null): 졸업요건 정보
- `show_requirements` (boolean): 졸업요건 표시 여부
- `evaluation` (object|null): 졸업요건 충족도 평가
- `show_evaluation` (boolean): 평가 결과 표시 여부
- `library_seats` (array|null): 도서관 좌석 현황
- `show_library_seats` (boolean): 좌석 정보 표시 여부
- `needs_library_login` (boolean): 도서관 로그인 필요 여부
- `meals` (object|null): 학식 메뉴 정보 (NEW)
  ```json
  {
    "cafeteria": "학생회관 학생식당",
    "menu": "깻잎제육덮밥",
    "price": "5,000원",
    "source_url": "https://khucoop.com/35",
    "menu_url": "https://khucoop.com/35"
  }
  ```
- `show_meals` (boolean): 학식 정보 표시 여부

---

## 🔧 성능 최적화

### 캐싱 전략

모든 Tool 호출은 Redis 캐싱을 거칩니다.

| Tool | 캐시 키 패턴 | TTL |
|------|-------------|-----|
| search_classroom | `search_classroom:query:{query}` | 24시간 |
| search_curriculum | `search_curriculum:query:{query}:year:{year}` | 24시간 |
| get_requirements | `get_requirements:program:{program}:year:{year}` | 24시간 |
| search_notices | `search_notices:query:{query}` | 2시간 |
| get_latest_notices | `get_latest_notices:department:{dept}` | 2시간 |
| get_library_info | `get_library_info:campus:{campus}` | 1시간 |
| get_today_meal | `get_today_meal:meal_type:{type}` | 1시간 |
| get_seat_availability | `get_seat_availability:campus:{campus}:user:{id}` | 1분 |

**캐시 히트 응답 시간**: ~10ms
**캐시 미스 응답 시간**: ~500ms (MCP 호출)

---

### Hybrid LLM/SLM 라우팅

```
Simple 질문 (60%)
├─ SLM Success (80%): 평균 1.0s
└─ LLM Fallback (20%): 평균 6.0s

Complex 질문 (40%): 평균 12.0s

Overall Average: 5.5s (기존 16.6s 대비 -67%)
```

**응답 헤더 추가**:
```
X-Routing-Decision: llm | slm | llm_fallback
X-Question-Type: simple | complex
X-Response-Time-Ms: 1234
X-Cache-Hit: true | false
```

---

## 📊 Observability

### 메트릭 수집

모든 `/api/chat` 호출은 Elasticsearch에 로깅됩니다.

**로그 구조** (Elasticsearch Index: `agent-khu-interactions`):
```json
{
  "timestamp": "2025-12-19T10:30:00Z",
  "question": "자료구조는 몇 학점이야?",
  "user_id": "2019104488",
  "question_type": "simple",
  "routing_decision": "slm",
  "mcp_tools_used": [],
  "response": "자료구조는 3학점입니다.",
  "latency_ms": 1024,
  "success": true,
  "error_message": null
}
```

**메트릭 조회** (관리자 전용):
```bash
# Kibana 대시보드
http://localhost:5601

# 평균 응답시간
GET /agent-khu-interactions/_search
{
  "aggs": {
    "avg_latency": {
      "avg": {"field": "latency_ms"}
    }
  }
}

# 라우팅 분포
GET /agent-khu-interactions/_search
{
  "aggs": {
    "routing_distribution": {
      "terms": {"field": "routing_decision"}
    }
  }
}
```

---

## 🔐 보안 업데이트

### JWT 토큰

**변경 없음**: JWT Bearer Token 방식 유지

**토큰 만료**: 1시간 (기본값)

### CORS 설정

```python
# main.py
allowed_origins = os.getenv(
    "CORS_ALLOW_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
).split(",")
```

**환경변수**:
```bash
CORS_ALLOW_ORIGINS=http://localhost:5173,https://agent-khu.com
```

---

## 📈 에러 핸들링

### 새로운 에러 코드

| Code | 의미 | 예시 |
|------|------|------|
| 429 | Too Many Requests | 캐시 미스 + Redis 과부하 |
| 503 | Service Unavailable | MCP 서버 타임아웃 |
| 424 | Failed Dependency | Elasticsearch 연결 실패 (로깅만 영향) |

### 에러 응답 형식 (업데이트)

```json
{
  "detail": "에러 메시지",
  "error_type": "MCP_TIMEOUT",
  "retry_after": 5,  // 초 단위
  "fallback_available": true
}
```

---

## 🧪 테스트

### cURL 예제

```bash
# 1. 로그인
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"student_id":"2019104488","password":"password"}' \
  | jq -r '.access_token')

# 2. 채팅 (Simple 질문)
curl -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"자료구조는 몇 학점이야?"}'

# 3. 교과과정 검색
curl -X GET "http://localhost:8000/api/curriculum/search?query=자료구조" \
  -H "Authorization: Bearer $TOKEN"

# 4. 졸업요건 조회 (자동으로 사용자 정보 사용)
curl -X GET http://localhost:8000/api/curriculum/requirements \
  -H "Authorization: Bearer $TOKEN"

# 5. 캐시 정보
curl -X GET http://localhost:8000/api/cache/info \
  -H "Authorization: Bearer $TOKEN"

# 6. 캐시 삭제 (패턴)
curl -X DELETE http://localhost:8000/api/cache/pattern \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pattern":"search_notices:*"}'
```

---

## 📚 Swagger UI

FastAPI 자동 생성 API 문서:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

**새로운 태그**:
- `cache` - 캐시 관리
- `curriculum` - 교과과정
- `observability` - 메트릭 (관리자 전용)

---

## 참고 자료

- [기존 API 문서](./API.md)
- [아키텍처 업데이트](./ARCHITECTURE_UPDATE.md)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Redis 캐싱 패턴](https://redis.io/docs/manual/patterns/)
