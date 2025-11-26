# Course MCP Server 📚

경희대학교 수강신청 사이트에서 개설 교과목 정보를 크롤링하는 MCP 서버입니다.

---

## ✨ 주요 기능

### 🤖 Playwright 자동화
- **헤드리스 브라우저**: Chromium 자동 제어
- **로그인 불필요**: 공개 정보만 크롤링
- **자동 재시도**: 네트워크 오류 대응

### ⚡ 1시간 캐싱
- 첫 요청: 크롤링 (5-10초)
- 이후 요청: 캐시 사용 (0.1초)
- 1시간 후 자동 갱신

### 🔍 상세 정보
- 과목명, 교수명
- 시간표, 강의실
- 정원, 수강인원
- 학점, 학년

---

## 🚀 빠른 시작

### 사전 준비

```bash
# Playwright 설치
pip install playwright

# 브라우저 설치
playwright install chromium
```

### 독립 실행

```bash
cd mcp-servers/course-mcp
python server.py
```

### JSON-RPC 테스트

```bash
# 초기화
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python server.py

# 과목 검색
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_courses","arguments":{"query":"자료구조"}}}' | python server.py

# 교수 검색
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"search_by_professor","arguments":{"professor":"홍길동"}}}' | python server.py

# 캐시 갱신
echo '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"refresh_courses","arguments":{}}}' | python server.py
```

---

## 🔧 Tools

### 1. search_courses

개설 교과목을 검색합니다.

**입력**
```json
{
  "query": "자료구조",
  "semester": "2025-1"
}
```

**출력**
```json
{
  "semester": "2025-1",
  "courses": [
    {
      "code": "CSE204-01",
      "name": "자료구조",
      "professor": "홍길동",
      "credits": 3,
      "time": "월(10:30-11:45), 수(10:30-11:45)",
      "room": "전자정보대학관 605호",
      "capacity": 60,
      "enrolled": 58,
      "year": 2,
      "category": "전공필수"
    }
  ],
  "count": 1,
  "cached": false,
  "updated_at": "2024-11-26T14:30:00"
}
```

---

### 2. search_by_professor

특정 교수의 강의를 검색합니다.

**입력**
```json
{
  "professor": "홍길동",
  "semester": "2025-1"
}
```

**출력**
```json
{
  "professor": "홍길동",
  "courses": [
    {
      "code": "CSE204-01",
      "name": "자료구조",
      "time": "월수(10:30-11:45)"
    },
    {
      "code": "CSE308-01",
      "name": "알고리즘",
      "time": "화목(13:00-14:15)"
    }
  ],
  "count": 2
}
```

---

### 3. get_course_details

과목 상세 정보를 조회합니다.

**입력**
```json
{
  "course_code": "CSE204-01",
  "semester": "2025-1"
}
```

**출력**
```json
{
  "code": "CSE204-01",
  "name": "자료구조",
  "professor": "홍길동",
  "credits": 3,
  "time": "월(10:30-11:45), 수(10:30-11:45)",
  "room": "전자정보대학관 605호",
  "capacity": 60,
  "enrolled": 58,
  "available": 2,
  "year": 2,
  "category": "전공필수",
  "description": "자료구조의 기본 개념과 응용"
}
```

---

### 4. refresh_courses

캐시를 무시하고 강제로 크롤링합니다.

**입력**
```json
{
  "semester": "2025-1"
}
```

**출력**
```json
{
  "success": true,
  "courses_count": 156,
  "updated_at": "2024-11-26T14:30:00",
  "message": "강의 목록이 업데이트되었습니다"
}
```

---

## 📂 디렉토리 구조

```
course-mcp/
├── server.py              # MCP 서버 메인
├── data/
│   └── courses_cache.json # 캐시 파일
└── README.md              # 이 파일
```

---

## 🔍 기술 상세

### Playwright 크롤링

```python
from playwright.async_api import async_playwright

async def crawl_courses(semester: str) -> List[Dict]:
    """수강신청 사이트 크롤링"""
    
    async with async_playwright() as p:
        # 브라우저 시작
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 수강신청 사이트 접속
        url = f"https://sugang.khu.ac.kr/courses?semester={semester}"
        await page.goto(url)
        
        # 페이지 로딩 대기
        await page.wait_for_selector('.course-list')
        
        # 과목 목록 파싱
        courses = []
        rows = await page.query_selector_all('.course-list tr')
        
        for row in rows:
            code = await row.query_selector('.code').text_content()
            name = await row.query_selector('.name').text_content()
            professor = await row.query_selector('.professor').text_content()
            
            courses.append({
                'code': code.strip(),
                'name': name.strip(),
                'professor': professor.strip()
            })
        
        await browser.close()
        
        return courses
```

### 캐싱 로직

```python
import json
from pathlib import Path
from datetime import datetime, timedelta

CACHE_PATH = Path(__file__).parent / "data/courses_cache.json"
CACHE_DURATION = timedelta(hours=1)

async def get_courses(semester: str, force_refresh: bool = False) -> List[Dict]:
    """캐시 우선 조회"""
    
    # 캐시 확인
    if CACHE_PATH.exists() and not force_refresh:
        with open(CACHE_PATH) as f:
            cache = json.load(f)
        
        updated_at = datetime.fromisoformat(cache['updated_at'])
        
        # 1시간 이내면 캐시 사용
        if datetime.now() - updated_at < CACHE_DURATION:
            return cache['courses'], True
    
    # 캐시 없거나 만료됨 → 크롤링
    courses = await crawl_courses(semester)
    
    # 캐시 저장
    cache = {
        'semester': semester,
        'courses': courses,
        'updated_at': datetime.now().isoformat()
    }
    
    CACHE_PATH.parent.mkdir(exist_ok=True)
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    
    return courses, False
```

---

## 🧪 테스트

### Playwright 설치 확인

```bash
# 버전 확인
playwright --version

# 브라우저 확인
playwright install --dry-run chromium
```

### 크롤링 테스트

```bash
# 수동 크롤링
python -c "
import asyncio
from server import crawl_courses

async def test():
    courses = await crawl_courses('2025-1')
    print(f'크롤링된 과목 수: {len(courses)}')
    print(f'첫 과목: {courses[0]}')

asyncio.run(test())
"
```

### 캐시 테스트

```bash
# 첫 요청 (크롤링)
time echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_courses","arguments":{"query":"자료구조"}}}' | python server.py

# 두 번째 요청 (캐시)
time echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_courses","arguments":{"query":"자료구조"}}}' | python server.py

# 속도 차이 확인 (크롤링: ~5초, 캐시: ~0.1초)
```

---

## 🐛 문제 해결

### 1. Playwright 오류

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

# 시스템 의존성 (Linux)
playwright install-deps
```

---

### 2. 크롤링 실패

```
TimeoutError: Timeout 30000ms exceeded
```

**해결**:
```python
# 타임아웃 연장
await page.goto(url, timeout=60000)  # 60초

# 재시도 로직
max_retries = 3
for i in range(max_retries):
    try:
        await page.goto(url)
        break
    except Exception as e:
        if i == max_retries - 1:
            raise
        await asyncio.sleep(2)
```

---

### 3. 선택자 오류

```
Error: No element matches selector '.course-list'
```

**해결**:
```python
# 선택자 확인
# 브라우저에서 개발자 도구로 실제 HTML 확인

# 대기 시간 연장
await page.wait_for_selector('.course-list', timeout=30000)

# 동적 로딩 대기
await page.wait_for_load_state('networkidle')
```

---

### 4. 캐시 초기화

```bash
# 캐시 파일 삭제
rm data/courses_cache.json

# 또는 강제 갱신
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"refresh_courses","arguments":{}}}' | python server.py
```

---

## 💡 사용 예시

### Agent에서 사용

**질문**: "자료구조 수업 시간표 알려줘"

**Agent 처리**:
```python
# 1. 과목 검색
result = await mcp_client.call_tool(
    "course",
    "search_courses",
    {"query": "자료구조", "semester": "2025-1"}
)

# 2. 응답 생성
course = result["courses"][0]
response = f"""
📚 자료구조 (CSE204-01)

👨‍🏫 교수: {course['professor']}
⏰ 시간: {course['time']}
📍 강의실: {course['room']}
👥 인원: {course['enrolled']}/{course['capacity']} (여석 {course['capacity'] - course['enrolled']})
"""
```

---

## ⚠️ 주의사항

### 1. 크롤링 부하

```python
# 너무 자주 크롤링하지 않도록 1시간 캐싱
CACHE_DURATION = timedelta(hours=1)

# 동시 요청 제한
semaphore = asyncio.Semaphore(1)  # 한 번에 1개만
```

### 2. 로봇 배제 표준

```python
# robots.txt 확인
# User-agent: *
# Disallow: /admin/
# Allow: /courses

# 공개 정보만 크롤링
```

### 3. 로그인 필요 없음

```python
# ✅ 공개 정보
- 과목명, 교수명
- 시간표, 강의실
- 정원, 수강인원

# ❌ 비공개 정보 (로그인 필요)
- 성적 조회
- 수강 신청
- 개인 시간표
```

---

## 🔮 향후 계획

- [ ] 실시간 정원 변동 모니터링
- [ ] 시간표 충돌 체크
- [ ] 학점 계산기
- [ ] 과목 평점/리뷰 연동
- [ ] 교수 평가 정보
- [ ] 선수과목 확인

---

## 📚 참고 자료

- [Playwright 공식 문서](https://playwright.dev/python/)
- [Playwright Python API](https://playwright.dev/python/docs/api/class-playwright)
- [경희대 수강신청 시스템](https://sugang.khu.ac.kr/)