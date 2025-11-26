# Classroom MCP Server 🏫

경희대학교 전자정보대학관 강의실 정보를 조회하는 MCP 서버입니다.

---

## ✨ 주요 기능

### 🔍 강의실 검색
- 호수별 검색 (예: "605호")
- 건물명 검색 (예: "전정대")
- 층별 검색

### 📍 위치 정보
- GPS 좌표 (위도/경도)
- 층수 정보
- 건물 안내

### 🗺️ 지도 렌더링
- 사용자 위치 기반 거리 계산
- 지도 표시 데이터 제공

---

## 🚀 빠른 시작

### 독립 실행

```bash
cd mcp-servers/classroom-mcp
python server.py
```

### JSON-RPC 테스트

```bash
# 초기화
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python server.py

# 강의실 검색
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_classroom","arguments":{"query":"605"}}}' | python server.py

# 층별 검색
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search_by_floor","arguments":{"floor":6}}}' | python server.py

# 거리 계산
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"get_nearest_classroom","arguments":{"user_latitude":37.2425,"user_longitude":127.0792,"query":"강의실"}}}' | python server.py
```

---

## 🔧 Tools

### 1. search_classroom

강의실을 검색합니다.

**입력**
```json
{
  "query": "605",
  "limit": 5
}
```

**출력**
```json
{
  "classrooms": [
    {
      "id": 1,
      "name": "전자정보대학관 605호",
      "building": "전자정보대학관",
      "room_number": "605",
      "floor": 6,
      "latitude": 37.2425,
      "longitude": 127.0792,
      "description": "강의실"
    }
  ],
  "count": 1
}
```

---

### 2. search_by_floor

특정 층의 강의실을 조회합니다.

**입력**
```json
{
  "floor": 6,
  "building": "전자정보대학관"
}
```

**출력**
```json
{
  "floor": 6,
  "building": "전자정보대학관",
  "classrooms": [
    {
      "name": "전자정보대학관 601호",
      "room_number": "601",
      "description": "강의실"
    },
    {
      "name": "전자정보대학관 605호",
      "room_number": "605",
      "description": "강의실"
    }
  ],
  "count": 2
}
```

---

### 3. get_nearest_classroom

사용자 위치에서 가장 가까운 강의실을 찾습니다.

**입력**
```json
{
  "user_latitude": 37.2425,
  "user_longitude": 127.0792,
  "query": "강의실",
  "limit": 3
}
```

**출력**
```json
{
  "user_location": {
    "latitude": 37.2425,
    "longitude": 127.0792
  },
  "nearest": [
    {
      "name": "전자정보대학관 605호",
      "distance_meters": 50,
      "latitude": 37.2425,
      "longitude": 127.0792,
      "floor": 6
    },
    {
      "name": "전자정보대학관 601호",
      "distance_meters": 80,
      "latitude": 37.2426,
      "longitude": 127.0793,
      "floor": 6
    }
  ]
}
```

---

### 4. get_classroom_details

강의실 상세 정보를 조회합니다.

**입력**
```json
{
  "classroom_id": 1
}
```

**출력**
```json
{
  "id": 1,
  "name": "전자정보대학관 605호",
  "building": "전자정보대학관",
  "room_number": "605",
  "floor": 6,
  "latitude": 37.2425,
  "longitude": 127.0792,
  "description": "강의실",
  "capacity": 60,
  "facilities": ["프로젝터", "화이트보드", "에어컨"]
}
```

---

## 📂 디렉토리 구조

```
classroom-mcp/
├── server.py              # MCP 서버 메인
└── README.md              # 이 파일
```

---

## 🔍 기술 상세

### 거리 계산 (Haversine Formula)

```python
import math

def calculate_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float
) -> float:
    """두 GPS 좌표 간 거리 계산 (미터)"""
    R = 6371000  # 지구 반지름 (미터)
    
    # 라디안 변환
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine 공식
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return round(distance, 1)
```

### 검색 로직

```python
async def tool_search_classroom(args: Dict) -> Dict:
    """강의실 검색"""
    query = args.get("query", "")
    limit = args.get("limit", 5)
    
    # DB 검색
    classrooms = db.query(Classroom).filter(
        or_(
            Classroom.name.contains(query),
            Classroom.room_number.contains(query),
            Classroom.building.contains(query)
        )
    ).limit(limit).all()
    
    return {
        "classrooms": [c.to_dict() for c in classrooms],
        "count": len(classrooms)
    }
```

---

## 🧪 테스트

### DB 데이터 삽입

```sql
-- 전자정보대학관 강의실
INSERT INTO classrooms (name, building, room_number, floor, latitude, longitude, description)
VALUES
  ('전자정보대학관 601호', '전자정보대학관', '601', 6, 37.2425, 127.0792, '강의실'),
  ('전자정보대학관 605호', '전자정보대학관', '605', 6, 37.2425, 127.0792, '강의실'),
  ('전자정보대학관 610호', '전자정보대학관', '610', 6, 37.2426, 127.0793, '세미나실');
```

또는:

```bash
# parse_rooms.py 실행
cd backend
python parse_rooms.py
```

### 검색 테스트

```bash
# 605호 검색
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_classroom","arguments":{"query":"605"}}}' | python server.py

# 전정대 검색
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_classroom","arguments":{"query":"전정대"}}}' | python server.py
```

### 거리 계산 테스트

```bash
# 사용자 위치에서 가까운 강의실
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_nearest_classroom","arguments":{"user_latitude":37.2425,"user_longitude":127.0792,"query":"강의실"}}}' | python server.py
```

---

## 🐛 문제 해결

### 1. 검색 결과 없음

```json
{
  "classrooms": [],
  "count": 0
}
```

**해결**:
```bash
# DB 데이터 확인
psql -U postgres -d agent_khu -c "SELECT * FROM classrooms;"

# 데이터 없으면 삽입
cd backend
python parse_rooms.py
```

### 2. GPS 좌표 오류

```
ValueError: latitude must be between -90 and 90
```

**해결**:
```python
# 좌표 범위 확인
# 위도: -90 ~ 90
# 경도: -180 ~ 180

# 경희대 서울캠퍼스 좌표
latitude = 37.2425
longitude = 127.0792
```

### 3. 거리 계산 오류

```
TypeError: unsupported operand type(s) for -: 'NoneType' and 'float'
```

**해결**:
```python
# GPS 좌표가 None인지 확인
if classroom.latitude is None or classroom.longitude is None:
    continue
```

---

## 💡 사용 예시

### Agent에서 사용

**질문**: "605호가 어디야?"

**Agent 처리**:
```python
# 1. 강의실 검색
result = await mcp_client.call_tool(
    "classroom",
    "search_classroom",
    {"query": "605"}
)

# 2. 지도 데이터 구성
classroom = result["classrooms"][0]
map_data = {
    "center": {
        "latitude": classroom["latitude"],
        "longitude": classroom["longitude"]
    },
    "markers": [
        {
            "name": classroom["name"],
            "latitude": classroom["latitude"],
            "longitude": classroom["longitude"]
        }
    ]
}

# 3. 응답 생성
response = f"""
📍 {classroom['name']}

🏢 건물: {classroom['building']}
📊 층: {classroom['floor']}층
📝 설명: {classroom['description']}

[지도 표시]
"""
```

**Frontend에서 지도 렌더링**:
```typescript
// map_data를 받아서 Leaflet/Google Maps로 표시
<Map
  center={[mapData.center.latitude, mapData.center.longitude]}
  markers={mapData.markers}
/>
```

---

## 🗺️ 지도 데이터 형식

```json
{
  "center": {
    "latitude": 37.2425,
    "longitude": 127.0792
  },
  "zoom": 17,
  "markers": [
    {
      "name": "전자정보대학관 605호",
      "latitude": 37.2425,
      "longitude": 127.0792,
      "icon": "classroom"
    }
  ]
}
```

---

## 📊 강의실 데이터

### 전자정보대학관

| 호수 | 층 | 용도 | 좌석 |
|------|-----|------|------|
| 601 | 6층 | 강의실 | 60 |
| 605 | 6층 | 강의실 | 60 |
| 610 | 6층 | 세미나실 | 30 |
| 701 | 7층 | 실습실 | 40 |

---

## 🔮 향후 계획

- [ ] 실시간 강의실 사용 현황
- [ ] 강의실 예약 시스템
- [ ] 실내 네비게이션
- [ ] AR 길찾기
- [ ] 강의실 리뷰/평점
- [ ] 다른 건물 추가

---

## 📚 참고 자료

- [Haversine Formula](https://en.wikipedia.org/wiki/Haversine_formula)
- [Leaflet (지도 라이브러리)](https://leafletjs.com/)
- [경희대학교 캠퍼스맵](https://www.khu.ac.kr/kor/campus/map.do)