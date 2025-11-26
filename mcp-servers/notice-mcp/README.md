# Notice MCP Server 📢

경희대학교 컴퓨터공학부 공지사항을 검색하는 MCP 서버입니다.

---

## ✨ 주요 기능

### 🔍 이중 검색 시스템
- **DB 우선 검색**: 캐시된 공지사항 빠른 조회
- **실시간 크롤링**: DB에 없으면 웹사이트 크롤링

### 📊 키워드 필터링
- 제목/내용 텍스트 검색
- 관련도 순 정렬

### ⚡ 성능
- DB 검색: 0.1초
- 크롤링: 3-5초

---

## 🚀 빠른 시작

### 독립 실행

```bash
cd mcp-servers/notice-mcp
python server.py
```

### JSON-RPC 테스트

```bash
# 초기화
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python server.py

# 공지사항 검색
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_notices","arguments":{"query":"수강신청"}}}' | python server.py

# 최신 공지 조회
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_latest_notices","arguments":{"limit":5}}}' | python server.py

# 실시간 크롤링
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"crawl_fresh_notices","arguments":{"query":"학사"}}}' | python server.py
```

---

## 🔧 Tools

### 1. search_notices

DB에서 공지사항을 검색합니다.

**입력**
```json
{
  "query": "수강신청",
  "limit": 10
}
```

**출력**
```json
{
  "notices": [
    {
      "id": 1,
      "title": "2025학년도 1학기 수강신청 안내",
      "content": "수강신청 일정을 안내드립니다...",
      "url": "https://ce.khu.ac.kr/ce/user/board/BD_selectBoardArticle.do?q_bbsCode=1032&q_bbscttSn=20241201",
      "date": "2024-12-01",
      "category": "학사"
    }
  ],
  "count": 1,
  "source": "database"
}
```

---

### 2. get_latest_notices

최신 공지사항을 조회합니다.

**입력**
```json
{
  "limit": 5
}
```

**출력**
```json
{
  "notices": [
    {
      "id": 1,
      "title": "2025학년도 1학기 수강신청 안내",
      "date": "2024-12-01"
    },
    {
      "id": 2,
      "title": "동계방학 중 도서관 운영 안내",
      "date": "2024-11-28"
    }
  ],
  "count": 5
}
```

---

### 3. crawl_fresh_notices

웹사이트를 실시간 크롤링합니다.

**입력**
```json
{
  "query": "학사",
  "limit": 10
}
```

**출력**
```json
{
  "notices": [
    {
      "title": "2025학년도 1학기 수강신청 안내",
      "url": "https://ce.khu.ac.kr/...",
      "date": "2024-12-01"
    }
  ],
  "count": 1,
  "source": "web_crawling"
}
```

---

## 📂 디렉토리 구조

```
notice-mcp/
├── server.py              # MCP 서버 메인
└── README.md              # 이 파일
```

---

## 🔍 기술 상세

### 이중 검색 로직

```python
async def tool_search_notices(args: Dict) -> Dict:
    query = args.get("query", "")
    limit = args.get("limit", 10)
    
    # 1. DB 검색 시도
    notices = db.query(Notice).filter(
        or_(
            Notice.title.contains(query),
            Notice.content.contains(query)
        )
    ).limit(limit).all()
    
    if notices:
        return {
            "notices": [n.to_dict() for n in notices],
            "source": "database"
        }
    
    # 2. DB에 없으면 크롤링
    notices = crawl_notices(query)
    
    # 3. DB에 저장
    for notice in notices:
        db.add(Notice(**notice))
    db.commit()
    
    return {
        "notices": notices,
        "source": "web_crawling"
    }
```

### 크롤링 로직

```python
def crawl_notices(query: str) -> List[Dict]:
    url = "https://ce.khu.ac.kr/ce/user/board/BD_selectBoardList.do?q_bbsCode=1032"
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    notices = []
    for row in soup.select('.board-list tr'):
        title = row.select_one('.title').text.strip()
        
        # 키워드 필터링
        if query and query not in title:
            continue
        
        notices.append({
            'title': title,
            'url': row.select_one('a')['href'],
            'date': row.select_one('.date').text.strip()
        })
    
    return notices
```

---

## 🧪 테스트

### DB 검색 테스트

```bash
# DB에 공지사항 추가
psql -U postgres -d agent_khu -c "
INSERT INTO notices (title, content, url, date)
VALUES ('수강신청 안내', '수강신청 일정...', 'http://...', '2024-12-01');
"

# 검색 테스트
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_notices","arguments":{"query":"수강신청"}}}' | python server.py
```

### 크롤링 테스트

```bash
# 실제 웹사이트 크롤링
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"crawl_fresh_notices","arguments":{"query":"학사"}}}' | python server.py
```

---

## 🐛 문제 해결

### 1. DB 연결 오류

```
sqlalchemy.exc.OperationalError: could not connect to database
```

**해결**:
```bash
# PostgreSQL 실행 확인
pg_isready

# DATABASE_URL 확인
echo $DATABASE_URL
```

### 2. 크롤링 실패

```
requests.exceptions.HTTPError: 404 Not Found
```

**해결**:
```bash
# URL 확인
curl -I https://ce.khu.ac.kr/ce/user/board/BD_selectBoardList.do?q_bbsCode=1032

# 수동 크롤링
python -c "
import requests
from bs4 import BeautifulSoup
url = 'https://ce.khu.ac.kr/ce/user/board/BD_selectBoardList.do?q_bbsCode=1032'
response = requests.get(url)
print(response.status_code)
"
```

### 3. 검색 결과 없음

```json
{
  "notices": [],
  "count": 0
}
```

**해결**:
- 검색어 확인
- DB 데이터 확인: `SELECT * FROM notices WHERE title LIKE '%수강신청%';`
- 크롤링 강제 실행: `crawl_fresh_notices` 사용

---

## 🔮 향후 계획

- [ ] 다른 학과 공지사항 추가
- [ ] 카테고리별 필터링 (학사/장학/행사)
- [ ] 이미지 첨부 파일 지원
- [ ] 공지사항 알림 기능
- [ ] 검색 결과 하이라이트

---

## 📚 참고 자료

- [경희대 컴퓨터공학부 공지사항](https://ce.khu.ac.kr/ce/user/board/BD_selectBoardList.do?q_bbsCode=1032)
- [BeautifulSoup 문서](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [SQLAlchemy 문서](https://docs.sqlalchemy.org/)