# Library MCP Server 📚

경희대학교 중앙도서관 정보를 조회하는 MCP 서버입니다.

---

## ✨ 주요 기능

### 📊 좌석 현황
- **실시간 좌석 정보**: 열람실별 좌석 현황
- **빈 자리 찾기**: 이용 가능한 좌석 검색
- **예약 기능**: 좌석 예약 (로그인 필요)

### ℹ️ 도서관 정보
- 운영 시간
- 층별 안내
- 위치 정보

### 🔐 인증
- **로그인 불필요**: 기본 정보, 좌석 현황
- **로그인 필요**: 좌석 예약

---

## 🚀 빠른 시작

### 독립 실행

```bash
cd mcp-servers/library-mcp
python server.py
```

### JSON-RPC 테스트

```bash
# 초기화
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python server.py

# 도서관 정보
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_library_info","arguments":{}}}' | python server.py

# 좌석 현황
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_seat_status","arguments":{}}}' | python server.py

# 빈 자리 찾기
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"find_available_seats","arguments":{"min_seats":10}}}' | python server.py

# 좌석 예약 (로그인 필요)
echo '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"reserve_seat","arguments":{"room":"1열람실","seat_number":"A-101","student_id":"2019104488","password":"****"}}}' | python server.py
```

---

## 🔧 Tools

### 1. get_library_info

도서관 기본 정보를 조회합니다.

**입력**
```json
{}
```

**출력**
```json
{
  "name": "중앙도서관",
  "campus": "서울",
  "address": "서울시 동대문구 경희대로 26",
  "phone": "02-961-0073",
  "hours": {
    "weekday": "09:00 - 22:00",
    "weekend": "09:00 - 18:00"
  },
  "floors": [
    {
      "floor": "1층",
      "facilities": ["데스크", "열람실1"]
    },
    {
      "floor": "2층",
      "facilities": ["열람실2", "그룹스터디룸"]
    }
  ]
}
```

---

### 2. get_seat_status

실시간 좌석 현황을 조회합니다.

**입력**
```json
{
  "room": "1열람실"
}
```

**room**: 선택사항, 생략 시 전체 열람실

**출력**
```json
{
  "timestamp": "2024-11-26T14:30:00",
  "rooms": [
    {
      "name": "1열람실",
      "total_seats": 120,
      "occupied_seats": 75,
      "available_seats": 45,
      "usage_rate": 62.5
    },
    {
      "name": "2열람실",
      "total_seats": 80,
      "occupied_seats": 68,
      "available_seats": 12,
      "usage_rate": 85.0
    }
  ],
  "total": {
    "total_seats": 200,
    "available_seats": 57,
    "usage_rate": 71.5
  }
}
```

---

### 3. find_available_seats

빈 자리가 많은 열람실을 찾습니다.

**입력**
```json
{
  "min_seats": 10
}
```

**출력**
```json
{
  "recommendations": [
    {
      "room": "1열람실",
      "available_seats": 45,
      "usage_rate": 62.5,
      "recommendation": "여유로움"
    },
    {
      "room": "2열람실",
      "available_seats": 12,
      "usage_rate": 85.0,
      "recommendation": "혼잡함"
    }
  ]
}
```

---

### 4. reserve_seat

좌석을 예약합니다 (로그인 필요).

**입력**
```json
{
  "room": "1열람실",
  "seat_number": "A-101",
  "student_id": "2019104488",
  "password": "your_password"
}
```

**출력**
```json
{
  "success": true,
  "reservation": {
    "room": "1열람실",
    "seat_number": "A-101",
    "reserved_at": "2024-11-26T14:30:00",
    "expires_at": "2024-11-26T18:30:00"
  }
}
```

**에러**
```json
{
  "success": false,
  "error": "이미 예약된 좌석입니다"
}
```

---

## 📂 디렉토리 구조

```
library-mcp/
├── server.py              # MCP 서버 메인
└── README.md              # 이 파일
```

---

## 🔍 기술 상세

### 좌석 현황 크롤링

```python
import requests
from bs4 import BeautifulSoup

def get_seat_status() -> Dict:
    """도서관 좌석 현황 크롤링"""
    url = "https://lib.khu.ac.kr/seat/status"
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    rooms = []
    for room_div in soup.select('.room-status'):
        name = room_div.select_one('.room-name').text.strip()
        total = int(room_div.select_one('.total-seats').text)
        occupied = int(room_div.select_one('.occupied-seats').text)
        available = total - occupied
        
        rooms.append({
            "name": name,
            "total_seats": total,
            "occupied_seats": occupied,
            "available_seats": available,
            "usage_rate": round(occupied / total * 100, 1)
        })
    
    return {
        "timestamp": datetime.now().isoformat(),
        "rooms": rooms
    }
```

### 좌석 예약 (로그인)

```python
async def reserve_seat(
    room: str,
    seat_number: str,
    student_id: str,
    password: str
) -> Dict:
    """좌석 예약 (도서관 시스템 로그인 필요)"""
    
    # 1. 로그인
    session = requests.Session()
    login_url = "https://lib.khu.ac.kr/login"
    login_data = {
        "id": student_id,
        "password": password
    }
    
    response = session.post(login_url, data=login_data)
    if response.status_code != 200:
        return {
            "success": False,
            "error": "로그인 실패"
        }
    
    # 2. 좌석 예약
    reserve_url = "https://lib.khu.ac.kr/seat/reserve"
    reserve_data = {
        "room": room,
        "seat": seat_number
    }
    
    response = session.post(reserve_url, data=reserve_data)
    if response.status_code == 200:
        return {
            "success": True,
            "reservation": {
                "room": room,
                "seat_number": seat_number,
                "reserved_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=4)).isoformat()
            }
        }
    else:
        return {
            "success": False,
            "error": "예약 실패 (좌석 없음 또는 이미 예약됨)"
        }
```

---

## 🧪 테스트

### 좌석 현황 테스트

```bash
# 실시간 좌석 현황
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_seat_status","arguments":{}}}' | python server.py

# 특정 열람실
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_seat_status","arguments":{"room":"1열람실"}}}' | python server.py
```

### 빈 자리 찾기 테스트

```bash
# 최소 10석 이상
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"find_available_seats","arguments":{"min_seats":10}}}' | python server.py
```

### 예약 테스트 (주의: 실제 예약됨!)

```bash
# ⚠️ 실제 좌석이 예약됩니다!
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"reserve_seat","arguments":{"room":"1열람실","seat_number":"A-101","student_id":"2019104488","password":"****"}}}' | python server.py
```

---

## 🐛 문제 해결

### 1. 크롤링 실패

```
requests.exceptions.HTTPError: 404 Not Found
```

**해결**:
```bash
# URL 확인
curl -I https://lib.khu.ac.kr/seat/status

# 수동 테스트
python -c "
import requests
response = requests.get('https://lib.khu.ac.kr/seat/status')
print(response.status_code)
print(response.text[:500])
"
```

### 2. 로그인 실패

```json
{
  "success": false,
  "error": "로그인 실패"
}
```

**해결**:
- 학번/비밀번호 확인
- 도서관 시스템 접속 가능 여부 확인
- 계정 상태 확인 (정지/만료)

### 3. 예약 실패

```json
{
  "success": false,
  "error": "이미 예약된 좌석입니다"
}
```

**해결**:
- 다른 좌석 선택
- `find_available_seats`로 빈 자리 확인
- 예약 시간 확인 (운영 시간 내)

---

## 💡 사용 예시

### Agent에서 사용

**질문**: "도서관에 공부할 자리 있어?"

**Agent 처리**:
```python
# 1. 좌석 현황 조회
seat_status = await mcp_client.call_tool(
    "library",
    "get_seat_status",
    {}
)

# 2. 빈 자리 찾기
available = await mcp_client.call_tool(
    "library",
    "find_available_seats",
    {"min_seats": 10}
)

# 3. 응답 생성
response = f"""
📚 도서관 좌석 현황 (14:30 기준)

📍 1열람실: 45석 이용 가능 (여유로움)
📍 2열람실: 12석 이용 가능 (혼잡함)

1열람실 추천드려요!
"""
```

---

## 🔐 보안 고려사항

### 비밀번호 처리

```python
# ❌ 나쁜 예: 로그에 비밀번호 노출
logger.info(f"Login: {student_id}, {password}")

# ✅ 좋은 예: 비밀번호 마스킹
logger.info(f"Login: {student_id}, {'*' * len(password)}")
```

### 세션 관리

```python
# 사용 후 세션 종료
try:
    session = requests.Session()
    # ... 작업 수행
finally:
    session.close()
```

---

## 🔮 향후 계획

- [ ] 좌석 예약 취소 기능
- [ ] 예약 이력 조회
- [ ] 그룹 스터디룸 예약
- [ ] 좌석 이용 통계
- [ ] 푸시 알림 (자리 생김)
- [ ] 스터디카페 연동

---

## 📚 참고 자료

- [경희대학교 중앙도서관](https://library.khu.ac.kr/)
- [Requests 문서](https://requests.readthedocs.io/)
- [BeautifulSoup 문서](https://www.crummy.com/software/BeautifulSoup/)