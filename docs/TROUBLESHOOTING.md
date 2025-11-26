# 문제 해결 가이드 🔧

Agent KHU 사용 중 발생할 수 있는 문제와 해결 방법을 정리했습니다.

---

## 📋 목차

- [설치 문제](#설치-문제)
- [API 및 인증 문제](#api-및-인증-문제)
- [데이터베이스 문제](#데이터베이스-문제)
- [MCP 서버 문제](#mcp-서버-문제)
- [Frontend 문제](#frontend-문제)
- [성능 문제](#성능-문제)

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

### CORS 오류

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