# Meal MCP Server 🍽️

경희대학교 학생식당 메뉴를 조회하는 MCP 서버입니다.

---

## ✨ 주요 기능

### 📅 날짜별 조회
- 오늘/내일/특정 날짜 메뉴 조회
- 주간 메뉴 일괄 조회

### 🏢 식당별 구분
- 학생식당
- 교직원식당
- 기숙사식당

### 🔍 메뉴 검색
- 키워드 기반 메뉴 검색
- 식단 필터링

---

## 🚀 빠른 시작

### 독립 실행

```bash
cd mcp-servers/meal-mcp
python server.py
```

### JSON-RPC 테스트

```bash
# 초기화
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python server.py

# 오늘 메뉴 조회
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_meals","arguments":{"date":"today"}}}' | python server.py

# 내일 메뉴 조회
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_meals","arguments":{"date":"tomorrow"}}}' | python server.py

# 특정 날짜 메뉴
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"get_meals","arguments":{"date":"2024-12-25"}}}' | python server.py

# 메뉴 검색
echo '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"search_meals","arguments":{"query":"김치찌개"}}}' | python server.py
```

---

## 🔧 Tools

### 1. get_meals

특정 날짜의 학식 메뉴를 조회합니다.

**입력**
```json
{
  "date": "today"
}
```

**date 형식**:
- `"today"`: 오늘
- `"tomorrow"`: 내일
- `"2024-12-25"`: 특정 날짜 (YYYY-MM-DD)

**출력**
```json
{
  "date": "2024-11-26",
  "day_of_week": "화요일",
  "meals": [
    {
      "location": "학생식당",
      "menu": [
        {
          "name": "김치찌개",
          "type": "메인",
          "price": 5000
        },
        {
          "name": "제육볶음",
          "type": "메인",
          "price": 5500
        },
        {
          "name": "된장찌개",
          "type": "국",
          "price": 4000
        }
      ]
    },
    {
      "location": "교직원식당",
      "menu": [
        {
          "name": "돈까스",
          "type": "메인",
          "price": 7000
        }
      ]
    }
  ]
}
```

---

### 2. search_meals

키워드로 메뉴를 검색합니다.

**입력**
```json
{
  "query": "김치찌개",
  "limit": 5
}
```

**출력**
```json
{
  "results": [
    {
      "date": "2024-11-26",
      "location": "학생식당",
      "menu": "김치찌개",
      "price": 5000
    },
    {
      "date": "2024-11-27",
      "location": "학생식당",
      "menu": "김치찌개",
      "price": 5000
    }
  ],
  "count": 2
}
```

---

### 3. get_weekly_meals

주간 메뉴를 조회합니다.

**입력**
```json
{
  "start_date": "2024-11-25"
}
```

**출력**
```json
{
  "week": "2024-11-25 ~ 2024-12-01",
  "meals": [
    {
      "date": "2024-11-25",
      "day": "월",
      "student": ["김치찌개", "제육볶음"],
      "staff": ["돈까스"]
    },
    {
      "date": "2024-11-26",
      "day": "화",
      "student": ["된장찌개", "불고기"],
      "staff": ["비빔밥"]
    }
  ]
}
```

---

## 📂 디렉토리 구조

```
meal-mcp/
├── server.py              # MCP 서버 메인
└── README.md              # 이 파일
```

---

## 🔍 기술 상세

### 날짜 파싱

```python
from datetime import datetime, timedelta

def parse_date(date_str: str) -> str:
    """날짜 문자열을 YYYY-MM-DD 형식으로 변환"""
    if date_str == "today":
        return datetime.now().strftime("%Y-%m-%d")
    elif date_str == "tomorrow":
        return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        # YYYY-MM-DD 형식 검증
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
```

### DB 조회

```python
async def tool_get_meals(args: Dict) -> Dict:
    date_str = parse_date(args.get("date", "today"))
    
    # DB에서 조회
    meals = db.query(Meal).filter(
        Meal.date == date_str
    ).all()
    
    if not meals:
        return {
            "date": date_str,
            "meals": [],
            "message": "등록된 메뉴가 없습니다"
        }
    
    # 식당별로 그룹화
    result = {}
    for meal in meals:
        if meal.location not in result:
            result[meal.location] = []
        result[meal.location].append({
            "name": meal.name,
            "type": meal.type,
            "price": meal.price
        })
    
    return {
        "date": date_str,
        "meals": [
            {"location": loc, "menu": menus}
            for loc, menus in result.items()
        ]
    }
```

---

## 🧪 테스트

### DB 데이터 삽입

```sql
-- 테스트 데이터 삽입
INSERT INTO meals (date, location, name, type, price)
VALUES
  ('2024-11-26', '학생식당', '김치찌개', '메인', 5000),
  ('2024-11-26', '학생식당', '제육볶음', '메인', 5500),
  ('2024-11-26', '교직원식당', '돈까스', '메인', 7000);
```

### 조회 테스트

```bash
# 오늘 메뉴
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_meals","arguments":{"date":"today"}}}' | python server.py

# 내일 메뉴
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_meals","arguments":{"date":"tomorrow"}}}' | python server.py
```

### 검색 테스트

```bash
# 김치찌개 검색
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search_meals","arguments":{"query":"김치찌개"}}}' | python server.py
```

---

## 🐛 문제 해결

### 1. 메뉴 없음

```json
{
  "meals": [],
  "message": "등록된 메뉴가 없습니다"
}
```

**해결**:
```bash
# DB 데이터 확인
psql -U postgres -d agent_khu -c "SELECT * FROM meals WHERE date = '2024-11-26';"

# 데이터 삽입
psql -U postgres -d agent_khu -c "
INSERT INTO meals (date, location, name, type, price)
VALUES ('2024-11-26', '학생식당', '김치찌개', '메인', 5000);
"
```

### 2. 날짜 형식 오류

```
ValueError: time data '2024/11/26' does not match format '%Y-%m-%d'
```

**해결**:
```bash
# 올바른 형식 사용
# ❌ 2024/11/26
# ✅ 2024-11-26
```

### 3. DB 연결 오류

```
sqlalchemy.exc.OperationalError
```

**해결**:
```bash
# DATABASE_URL 확인
echo $DATABASE_URL

# PostgreSQL 실행 확인
pg_isready
```

---

## 💡 사용 예시

### Agent에서 사용

```python
# agent.py
async def process_tool_call(tool_name: str, tool_input: Dict):
    if tool_name == "get_meals":
        result = await mcp_client.call_tool(
            "meal",
            "get_meals",
            tool_input
        )
        return result
```

### 사용자 질문 예시

**질문**: "내일 학식 메뉴 뭐야?"

**Agent 처리**:
1. Tool 선택: `get_meals`
2. 인자: `{"date": "tomorrow"}`
3. MCP 호출
4. 응답:
```
내일(11월 27일 수요일) 학식 메뉴를 알려드릴게요!

📍 학생식당
- 김치찌개 (5,000원)
- 제육볶음 (5,500원)
- 된장찌개 (4,000원)

📍 교직원식당
- 돈까스 (7,000원)
```

---

## 🔮 향후 계획

- [ ] 실시간 메뉴 크롤링 추가
- [ ] 영양 정보 제공
- [ ] 식당 운영 시간 정보
- [ ] 메뉴 평점 시스템
- [ ] 기숙사 식당 메뉴 추가
- [ ] 이미지 지원

---

## 📚 참고 자료

- [경희대학교 생활관 식단표](https://dorm.khu.ac.kr/)
- [SQLAlchemy 문서](https://docs.sqlalchemy.org/)
- [Python datetime](https://docs.python.org/3/library/datetime.html)