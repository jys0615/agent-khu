# 설치 가이드 📦

Agent KHU를 설치하는 다양한 방법을 안내합니다.

---

## 📋 목차

- [요구사항](#요구사항)
- [Docker Compose (권장)](#docker-compose-권장)
- [수동 설치](#수동-설치)
- [환경변수 설정](#환경변수-설정)
- [데이터베이스 초기화](#데이터베이스-초기화)
- [MCP 서버 설정](#mcp-서버-설정)
- [문제 해결](#문제-해결)

---

## 요구사항

### 필수
- **Python 3.9+**
- **Node.js 18+**
- **PostgreSQL 15+**
- **Git**

### 선택 (권장)
- **Docker & Docker Compose**
- **Playwright** (course-mcp 사용 시)

### API 키
- **Anthropic API Key** (필수) - [console.anthropic.com](https://console.anthropic.com/)

---

## Docker Compose (권장)

가장 빠르고 간편한 방법입니다.

### 1. 저장소 클론

```bash
git clone https://github.com/YOUR_USERNAME/agent-khu.git
cd agent-khu
```

### 2. 환경변수 설정

```bash
# Backend 환경변수
cp backend/.env.example backend/.env

# Frontend 환경변수
cp frontend/.env.example frontend/.env
```

**backend/.env 편집:**
```bash
nano backend/.env
# 또는
code backend/.env
```

**필수 설정:**
```env
# Anthropic API (필수!)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Database (Docker Compose 기본값)
DATABASE_URL=postgresql://postgres:password@postgres:5432/agent_khu

# CORS (개발 환경 기본값)
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:3000

# MCP 설정 (선택)
MCP_AUTOSTART=true
MCP_INIT_TIMEOUT=10
MCP_CALL_TIMEOUT=60
```

**frontend/.env 편집:**
```env
VITE_API_URL=http://localhost:8000
```

### 3. Docker Compose 실행

```bash
# 컨테이너 빌드 & 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 특정 서비스만 로그 보기
docker-compose logs -f backend
```

### 4. 데이터베이스 초기화

```bash
# DB 테이블 생성
docker-compose exec backend python init_db.py

# 샘플 데이터 추가 (선택)
docker-compose exec backend python init_shuttle.py
docker-compose exec backend python parse_rooms.py
```

### 5. 접속

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432

### 6. 종료 & 재시작

```bash
# 종료
docker-compose down

# 재시작
docker-compose up -d

# 완전 삭제 (데이터 포함)
docker-compose down -v
```

---

## 수동 설치

Docker 없이 직접 설치하는 방법입니다.

### 1. PostgreSQL 설치

**macOS**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian**
```bash
sudo apt update
sudo apt install postgresql-15
sudo systemctl start postgresql
```

**데이터베이스 생성**
```bash
sudo -u postgres psql
```
```sql
CREATE DATABASE agent_khu;
CREATE USER postgres WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE agent_khu TO postgres;
\q
```

### 2. Backend 설치

```bash
cd backend

# 가상환경 생성
python3 -m venv venv

# 활성화
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt

# Playwright 설치 (course-mcp 사용 시)
playwright install chromium
```

### 3. Frontend 설치

```bash
cd frontend

# 의존성 설치
npm install
```

### 4. 환경변수 설정

```bash
# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.example frontend/.env
```

**backend/.env 편집:**
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
DATABASE_URL=postgresql://postgres:password@localhost:5432/agent_khu
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:3000
```

**frontend/.env 편집:**
```env
VITE_API_URL=http://localhost:8000
```

### 5. 데이터베이스 초기화

```bash
cd backend
python init_db.py
python init_shuttle.py  # 선택
python parse_rooms.py   # 선택
```

### 6. 서버 실행

**Backend (터미널 1)**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Frontend (터미널 2)**
```bash
cd frontend
npm run dev
```

### 7. 접속

- Frontend: http://localhost:5173
- Backend: http://localhost:8000

---

## 환경변수 설정

### Backend 환경변수

**필수**
```env
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/agent_khu
```

**선택 (기본값 있음)**
```env
# Server
HOST=0.0.0.0
PORT=8000

# CORS
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:3000

# JWT
JWT_SECRET_KEY=your-secret-key-change-this
ACCESS_TOKEN_EXPIRE_MINUTES=60

# MCP
MCP_AUTOSTART=true
MCP_INIT_TIMEOUT=10
MCP_CALL_TIMEOUT=60
MCP_ROOT=/path/to/mcp-servers  # 자동 감지됨
```

### Frontend 환경변수

```env
# API URL
VITE_API_URL=http://localhost:8000
```

---

## 데이터베이스 초기화

### 1. 기본 테이블 생성

```bash
cd backend
python init_db.py
```

**생성되는 테이블:**
- `users` - 사용자 정보
- `classrooms` - 강의실 정보
- `notices` - 공지사항
- `meals` - 학식 메뉴
- `library_seats` - 도서관 좌석
- `shuttle_buses` - 셔틀버스
- `courses` - 강의 정보
- `curriculums` - 교과과정

### 2. 초기 데이터 삽입

**셔틀버스 시간표**
```bash
python init_shuttle.py
```

**강의실 정보**
```bash
python parse_rooms.py
```

### 3. 수동 SQL 실행

```bash
psql -U postgres -d agent_khu -f scripts/init_data.sql
```

---

## MCP 서버 설정

### 자동 감지

MCP Client는 다음 순서로 서버 디렉토리를 찾습니다:

1. 환경변수 `MCP_ROOT`
2. 프로젝트 루트 기준 `../mcp-servers`
3. 실행 위치 기준 `../mcp-servers`
4. 홈 디렉토리 `~/Desktop/agent-khu/mcp-servers`

### 수동 설정

```env
# backend/.env
MCP_ROOT=/path/to/agent-khu/mcp-servers
```

### 개별 MCP 서버 테스트

```bash
cd mcp-servers/curriculum-mcp

# JSON-RPC 요청
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python server.py

# 결과 확인
# {"jsonrpc": "2.0", "id": 1, "result": {...}}
```

---

## 문제 해결

### 1. Anthropic API 키 오류

```
Error: Anthropic API key is required
```

**해결:**
```bash
# .env 파일 확인
cat backend/.env | grep ANTHROPIC

# 키가 없다면
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" >> backend/.env
```

### 2. PostgreSQL 연결 오류

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**해결:**
```bash
# PostgreSQL 실행 상태 확인
pg_isready

# 실행 중이 아니면
brew services start postgresql@15  # macOS
sudo systemctl start postgresql    # Linux

# DATABASE_URL 확인
echo $DATABASE_URL
```

### 3. MCP 서버 시작 실패

```
❌ MCP 'curriculum' 시작 실패: FileNotFoundError
```

**해결:**
```bash
# MCP 디렉토리 확인
ls -la mcp-servers/

# 경로 수동 설정
export MCP_ROOT=/path/to/agent-khu/mcp-servers
```

### 4. Playwright 오류 (course-mcp)

```
playwright._impl._api_types.Error: Browser executable doesn't exist
```

**해결:**
```bash
# Playwright 브라우저 설치
playwright install chromium

# 전체 재설치
pip install playwright
playwright install
```

### 5. CORS 오류 (Frontend)

```
Access to fetch at 'http://localhost:8000' has been blocked by CORS policy
```

**해결:**
```env
# backend/.env
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 6. Port 충돌

```
Error: Address already in use
```

**해결:**
```bash
# 포트 사용 프로세스 찾기
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# 프로세스 종료
kill -9 <PID>

# 또는 다른 포트 사용
uvicorn app.main:app --port 8001
```

---

## 다음 단계

설치가 완료되었다면:

1. **[설정 가이드](CONFIGURATION.md)** - 상세 설정 방법
2. **[API 문서](API.md)** - API 엔드포인트 활용
3. **[MCP 서버 개발](MCP_SERVERS.md)** - 새 서버 추가 방법

---

## 추가 도움

- 📖 [문제 해결 가이드](TROUBLESHOOTING.md)
- 💬 [GitHub Discussions](https://github.com/YOUR_USERNAME/agent-khu/discussions)
- 🐛 [Issue 제보](https://github.com/YOUR_USERNAME/agent-khu/issues)