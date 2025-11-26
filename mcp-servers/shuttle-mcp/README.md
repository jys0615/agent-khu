# Shuttle MCP Server 🚌

경희대학교 셔틀버스 정보를 조회하는 MCP 서버입니다.

---

## ✨ 주요 기능

### 🕐 실시간 도착 정보
- 다음 버스 도착 시간
- 노선별 시간표
- 운행 상태

### 🗺️ 노선 정보
- 서울-국제 캠퍼스 순환
- 정류장 위치
- 소요 시간

### ⚡ 빠른 응답
- DB 기반 조회 (0.1초)
- 시간표 데이터 사전 로드

---

## 🚀 빠른 시작

### 독립 실행

```bash
cd mcp-servers/shuttle-mcp
python server.py
```

### JSON-RPC 테스트

```bash
# 초기화
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python server.py

# 다음 버스 조회
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_next_shuttle","arguments":{"from":"서울","to":"국제"}}}' | python server.py

# 전체 시간표
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_shuttle_schedule","arguments":{"route":"서울-국제"}}}' | python server.py

# 운행 중 확인
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"is_shuttle_running","arguments":{}}}' | python server.py
```

---

## 🔧 Tools

### 1. get_next_shuttle

다음 셔틀버스 도착 시간을 조회합니다.

**입력**
```json
{
  "from": "서울",
  "to": "국제"
}
```

**from/to**:
- `"서울"`: 서울캠퍼스
- `"국제"`: 국제캠퍼스

**출력**
```json
{
  "route": "서울 → 국제",
  "current_time": "14:35",
  "next_buses": [
    {
      "departure_time": "14:40",
      "minutes_left": 5,
      "status": "곧 출발"
    },
    {
      "departure_time": "15:00",
      "minutes_left": 25,
      "status": "대기 중"
    },
    {
      "departure_time": "15:20",
      "minutes_left": 45,
      "status": "대기 중"
    }
  ],
  "travel_time": "약 30분"
}
```

---

### 2. get_shuttle_schedule

전체 시간표를 조회합니다.

**입력**
```json
{
  "route": "서울-국제",
  "day_type": "weekday"
}
```

**route**:
- `"서울-국제"`: 서울 → 국제
- `"국제-서울"`: 국제 → 서울

**day_type**:
- `"weekday"`: 평일
- `"weekend"`: 주말

**출력**
```json
{
  "route": "서울 → 국제",
  "day_type": "평일",
  "schedules": [
    {
      "time": "08:00",
      "type": "일반"
    },
    {
      "time": "08:20",
      "type": "일반"
    },
    {
      "time": "09:00",
      "type": "직행"
    }
  ],
  "total_count": 25,
  "first_bus": "08:00",
  "last_bus": "18:00"
}
```

---

### 3. is_shuttle_running

현재 셔틀버스 운행 여부를 확인합니다.

**입력**
```json
{}
```

**출력**
```json
{
  "running": true,
  "current_time": "14:35",
  "message": "정상 운행 중입니다",
  "next_bus": {
    "route": "서울 → 국제",
    "time": "14:40",
    "minutes_left": 5
  }
}
```

**운행 종료 시**
```json
{
  "running": false,
  "current_time": "20:00",
  "message": "금일 운행이 종료되었습니다",
  "next_bus": {
    "date": "2024-11-27",
    "time": "08:00"
  }
}
```

---

## 📂 디렉토리 구조

```
shuttle-mcp/
├── server.py              # MCP 서버 메인
└── README.md              # 이 파일
```

---

## 🔍 기술 상세

### 다음 버스 계산

```python
from datetime import datetime, timedelta

def get_next_shuttle(from_campus: str, to_campus: str) -> Dict:
    """다음 셔틀버스 조회"""
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    
    # DB에서 시간표 조회
    route = f"{from_campus}-{to_campus}"
    schedules = db.query(ShuttleBus).filter(
        ShuttleBus.route == route,
        ShuttleBus.time >= current_time
    ).order_by(ShuttleBus.time).limit(3).all()
    
    next_buses = []
    for schedule in schedules:
        departure = datetime.strptime(schedule.time, "%H:%M")
        departure = now.replace(
            hour=departure.hour,
            minute=departure.minute,
            second=0,
            microsecond=0
        )
        
        minutes_left = int((departure - now).total_seconds() / 60)
        
        # 상태 결정
        if minutes_left <= 5:
            status = "곧 출발"
        elif minutes_left <= 10:
            status = "탑승 가능"
        else:
            status = "대기 중"
        
        next_buses.append({
            "departure_time": schedule.time,
            "minutes_left": minutes_left,
            "status": status
        })
    
    return {
        "route": f"{from_campus} → {to_campus}",
        "current_time": current_time,
        "next_buses": next_buses
    }
```

### 운행 여부 판단

```python
def is_shuttle_running() -> Dict:
    """셔틀버스 운행 여부 확인"""
    now = datetime.now()
    current_time = now.time()
    
    # 운행 시간: 08:00 ~ 18:00
    start_time = datetime.strptime("08:00", "%H:%M").time()
    end_time = datetime.strptime("18:00", "%H:%M").time()
    
    if start_time <= current_time <= end_time:
        # 다음 버스 조회
        next_bus = get_next_shuttle("서울", "국제")
        
        return {
            "running": True,
            "current_time": now.strftime("%H:%M"),
            "message": "정상 운행 중입니다",
            "next_bus": next_bus["next_buses"][0] if next_bus["next_buses"] else None
        }
    else:
        # 익일 첫차
        tomorrow = now + timedelta(days=1)
        
        return {
            "running": False,
            "current_time": now.strftime("%H:%M"),
            "message": "금일 운행이 종료되었습니다",
            "next_bus": {
                "date": tomorrow.strftime("%Y-%m-%d"),
                "time": "08:00"
            }
        }
```

---

## 🧪 테스트

### DB 데이터 삽입

```sql
-- 서울 → 국제 시간표
INSERT INTO shuttle_buses (route, time, type, day_type)
VALUES
  ('서울-국제', '08:00', '일반', 'weekday'),
  ('서울-국제', '08:20', '일반', 'weekday'),
  ('서울-국제', '09:00', '직행', 'weekday'),
  ('서울-국제', '09:20', '일반', 'weekday'),
  ('서울-국제', '10:00', '일반', 'weekday');

-- 국제 → 서울 시간표
INSERT INTO shuttle_buses (route, time, type, day_type)
VALUES
  ('국제-서울', '08:30', '일반', 'weekday'),
  ('국제-서울', '09:00', '일반', 'weekday'),
  ('국제-서울', '09:30', '직행', 'weekday');
```

### 조회 테스트

```bash
# 다음 버스
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_next_shuttle","arguments":{"from":"서울","to":"국제"}}}' | python server.py

# 시간표
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_shuttle_schedule","arguments":{"route":"서울-국제","day_type":"weekday"}}}' | python server.py
```

---

## 🐛 문제 해결

### 1. 다음 버스 없음

```json
{
  "next_buses": []
}
```

**해결**:
```bash
# 현재 시각 이후 버스 확인
psql -U postgres -d agent_khu -c "
SELECT * FROM shuttle_buses 
WHERE route = '서울-국제' 
AND time >= '14:35' 
ORDER BY time LIMIT 3;
"

# 데이터 없으면 삽입
python init_shuttle.py
```

### 2. DB 연결 오류

```
sqlalchemy.exc.OperationalError
```

**해결**:
```bash
# DATABASE_URL 확인
echo $DATABASE_URL

# PostgreSQL 실행
pg_isready
brew services start postgresql@15
```

### 3. 시간 계산 오류

```
ValueError: time data does not match format
```

**해결**:
```python
# 시간 형식 확인
# DB에 저장된 형식: "HH:MM" (예: "08:00")
# 비교 시 동일한 형식 사용
```

---

## 💡 사용 예시

### Agent에서 사용

**질문**: "지금 서울에서 국제 가는 버스 있어?"

**Agent 처리**:
```python
# 1. 다음 버스 조회
result = await mcp_client.call_tool(
    "shuttle",
    "get_next_shuttle",
    {"from": "서울", "to": "국제"}
)

# 2. 응답 생성
next_bus = result["next_buses"][0]
response = f"""
🚌 서울 → 국제 다음 버스

⏰ {next_bus['departure_time']} 출발
⏳ {next_bus['minutes_left']}분 후
📍 상태: {next_bus['status']}

🕐 소요시간: 약 30분
"""
```

---

## 📊 시간표 데이터

### 평일 (서울 → 국제)

| 시간 | 유형 | 비고 |
|------|------|------|
| 08:00 | 일반 | 첫차 |
| 08:20 | 일반 | |
| 09:00 | 직행 | 빠름 |
| 09:20 | 일반 | |
| 10:00 | 일반 | |
| ... | ... | |
| 18:00 | 일반 | 막차 |

### 주말 (서울 → 국제)

| 시간 | 유형 | 비고 |
|------|------|------|
| 09:00 | 일반 | 첫차 |
| 10:00 | 일반 | |
| 11:00 | 일반 | |
| ... | ... | |
| 17:00 | 일반 | 막차 |

---

## 🔮 향후 계획

- [ ] 실시간 GPS 위치 추적
- [ ] 지연/결행 정보
- [ ] 혼잡도 정보
- [ ] 푸시 알림 (출발 5분 전)
- [ ] 노선 지도 표시
- [ ] 예약 시스템

---

## 📚 참고 자료

- [경희대학교 셔틀버스 안내](https://www.khu.ac.kr/kor/campus/shuttle.do)
- [Python datetime](https://docs.python.org/3/library/datetime.html)
- [SQLAlchemy 문서](https://docs.sqlalchemy.org/)