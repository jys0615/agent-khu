# Curriculum MCP Server 📚

경희대학교 소프트웨어융합대학 교과과정 데이터를 제공하는 MCP 서버입니다.

---

## ✨ 주요 기능

### 🔄 자동 갱신
- **24시간 주기** 자동 크롤링
- **SHA256 해시** 기반 변경 감지
- 변경사항 있을 때만 업데이트

### 🎯 정확한 파싱
- **HTML rowspan 속성** 완벽 처리
- **15개/14개 셀** 자동 구분
- **76개 과목** 정확히 파싱

### ⚡ 빠른 응답
- **로컬 JSON 캐시** 우선 사용
- 크롤링 5초 → 캐시 0.1초
- Lazy update (백그라운드)

---

## 🚀 빠른 시작

### 독립 실행

```bash
cd mcp-servers/curriculum-mcp
python server.py
```

### JSON-RPC 테스트

```bash
# 초기화
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python server.py

# 과목 검색
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_courses","arguments":{"query":"자료구조"}}}' | python server.py

# 강제 업데이트
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"force_update","arguments":{}}}' | python server.py
```

---

## 🔧 Tools

### 1. search_courses

과목을 검색합니다.

**입력**
```json
{
  "query": "자료구조",
  "year": "latest"
}
```

**출력**
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

### 2. list_programs

전공 프로그램 목록을 조회합니다.

**입력**
```json
{
  "year": "latest"
}
```

**출력**
```json
{
  "year": "2025",
  "programs": ["KHU-CSE"]
}
```

### 3. get_requirements

졸업요건을 조회합니다.

**입력**
```json
{
  "program": "KHU-CSE",
  "year": "latest"
}
```

**출력**
```json
{
  "program": "KHU-CSE",
  "year": "2025",
  "name": "컴퓨터공학전공",
  "total_credits": 130,
  "groups": [
    {
      "key": "major_basic",
      "name": "전공기초",
      "min_credits": 12
    },
    ...
  ]
}
```

### 4. force_update

수동으로 데이터를 업데이트합니다.

**입력**
```json
{}
```

**출력**
```json
{
  "success": true,
  "message": "업데이트 완료",
  "timestamp": "2025-11-26T14:18:32.614876"
}
```

---

## 📂 디렉토리 구조

```
curriculum-mcp/
├── server.py                    # MCP 서버 메인
├── scrapers/
│   └── curriculum_scraper.py    # 크롤링 로직
├── data/
│   ├── curriculum_data.json     # 교과과정 데이터
│   └── cache.json               # 캐시 메타데이터
└── README.md                    # 이 파일
```

---

## 🔍 기술 상세

### HTML rowspan 처리

경희대 교과과정 페이지는 `rowspan` 속성을 사용하여 여러 행에 걸쳐 셀을 병합합니다.

**문제 상황**
```html
<!-- Row 1: 15개 셀 -->
<tr>
  <td>1</td>
  <td rowspan="4">전공 필수</td>  <!-- 4개 행 공유 -->
  <td>미분방정식</td>
  <td>AMTH1001</td>
  ...
</tr>

<!-- Row 2: 14개 셀 (이수구분 없음!) -->
<tr>
  <td>2</td>
  <!-- 이수구분 셀 생략 -->
  <td>선형대수</td>      <!-- cells[1] -->
  <td>AMTH1004</td>      <!-- cells[2] -->
  ...
</tr>
```

**해결 방법**
```python
last_group = ""  # rowspan 처리용

for row in rows:
    cells = [td.text for td in row.xpath(".//td")]
    
    # 셀 개수로 rowspan 감지
    if len(cells) >= 15:
        # 정상 행 (이수구분 포함)
        group = cells[1]
        name = cells[2]
        code = cells[3]
        sem1_idx = 10
        sem2_idx = 11
        last_group = group  # 저장
    else:
        # rowspan 행 (이수구분 생략)
        group = last_group  # 이전 값 사용
        name = cells[1]     # 한 칸 앞으로
        code = cells[2]
        sem1_idx = 9        # 한 칸 앞으로
        sem2_idx = 10
```

### 자동 갱신 메커니즘

```python
# 24시간마다 백그라운드 업데이트
UPDATE_INTERVAL = 86400  # 초

async def background_updater():
    while True:
        await update_curriculum_data()
        await asyncio.sleep(UPDATE_INTERVAL)

# 변경 감지 (SHA256 해시)
def calculate_hash(data: dict) -> str:
    serialized = json.dumps(data, sort_keys=True)
    return hashlib.sha256(serialized.encode()).hexdigest()

# 해시 비교
if new_hash != old_hash:
    save_data(new_data)
    print("🔄 변경 감지! 데이터 업데이트")
else:
    print("✅ 변경 없음")
```

---

## 📊 데이터 구조

### curriculum_data.json

```json
{
  "2025": {
    "year": "2025",
    "programs": {
      "KHU-CSE": {
        "name": "컴퓨터공학전공",
        "total_credits": 130,
        "groups": [...]
      }
    },
    "catalog": [
      {
        "code": "CSE204",
        "name": "자료구조",
        "credits": 3,
        "group": "전공 필수",
        "semesters": ["1", "2"]
      },
      ...
    ],
    "crawled_at": "2025-11-26T14:18:32.614876"
  }
}
```

### cache.json

```json
{
  "last_hash": "a3f5c2...",
  "last_crawl": "2025-11-26T14:18:32.614876"
}
```

---

## 🧪 테스트

### 단위 테스트

```bash
# 크롤링 테스트
python -c "
from scrapers.curriculum_scraper import crawl_ce_curriculum
result = crawl_ce_curriculum()
print(f'과목 수: {len(result.get(\"catalog\", []))}')
"

# 자료구조 검증
python -c "
from server import load_data
data = load_data()
catalog = data['2025']['catalog']
cse204 = next((c for c in catalog if c['code'] == 'CSE204'), None)
assert cse204['name'] == '자료구조'
assert cse204['credits'] == 3
print('✅ 검증 완료')
"
```

### MCP 통신 테스트

```bash
# test_mcp.sh
cd ~/Desktop/agent-khu/mcp-servers/curriculum-mcp

echo "1. Initialize"
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python server.py

echo "2. Search 자료구조"
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_courses","arguments":{"query":"자료구조"}}}' | python server.py

echo "3. Force Update"
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"force_update","arguments":{}}}' | python server.py
```

---

## 🐛 문제 해결

### 1. 크롤링 실패

```
❌ 크롤링 실패: HTTPError 404
```

**원인**: URL 변경 또는 네트워크 오류

**해결**:
```bash
# URL 확인
curl -I https://ce.khu.ac.kr/ce/user/contents/view.do?menuNo=1600054

# 수동 크롤링
python scrapers/curriculum_scraper.py
```

### 2. rowspan 파싱 오류

```json
{
  "code": "CSE204",
  "name": "3",
  "credits": 2
}
```

**원인**: rowspan 로직 버그

**해결**:
```python
# 디버그 모드 활성화
DEBUG = True

# 처음 10개 행 출력
for idx, row in enumerate(rows[:10]):
    cells = [td.text for td in row.xpath(".//td")]
    print(f"Row {idx}: cells={len(cells)}, {cells[:5]}")
```

### 3. 캐시 초기화

```bash
# 캐시 파일 삭제
rm data/curriculum_data.json
rm data/cache.json

# 재크롤링
python server.py
```

---

## 🔮 향후 계획

- [ ] 인공지능학과 교과과정 추가
- [ ] 학기별 시간표 추가
- [ ] 선수과목 관계도 추가
- [ ] 교과목 해설 추가
- [ ] 교수별 과목 조회
- [ ] 수강평 연동

---

## 📚 참고 자료

- [경희대 컴퓨터공학부 교과과정](https://ce.khu.ac.kr/ce/user/contents/view.do?menuNo=1600054)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)

---

## 📞 문의

문제가 있거나 개선 제안이 있다면:
- GitHub Issues
- Pull Request
- Email: [YOUR_EMAIL]