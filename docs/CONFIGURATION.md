# 환경변수 및 설정 가이드 ⚙️

Agent KHU의 모든 설정 옵션을 상세히 설명합니다.

---

## 📋 목차

- [환경변수 개요](#환경변수-개요)
- [Backend 환경변수](#backend-환경변수)
- [Frontend 환경변수](#frontend-환경변수)
- [개발/프로덕션 설정](#개발프로덕션-설정)
- [보안 권장사항](#보안-권장사항)

---

## 환경변수 개요

### 파일 위치

```
backend/.env          # Backend 환경변수 (Git 제외)
backend/.env.example  # Backend 템플릿
frontend/.env         # Frontend 환경변수 (Git 제외)
frontend/.env.example # Frontend 템플릿
```

### 환경변수 우선순위

1. **시스템 환경변수** (export로 설정)
2. **.env 파일**
3. **코드 기본값**

---

## Backend 환경변수

### 필수 환경변수

#### ANTHROPIC_API_KEY

Claude AI API 키입니다.

**발급 방법**:
1. https://console.anthropic.com/ 접속
2. 로그인/회원가입
3. API Keys 메뉴에서 생성

**형식**:
```env
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

**주의사항**:
- 절대 Git에 커밋하지 마세요
- 주기적으로 재발급 권장
- 사용량 모니터링 필수

---

#### DATABASE_URL

PostgreSQL 연결 정보입니다.

**형식**:
```env
DATABASE_URL=postgresql://username:password@host:port/database
```

**예시**:
```env
# 로컬 개발
DATABASE_URL=postgresql://postgres:password@localhost:5432/agent_khu

# Docker Compose
DATABASE_URL=postgresql://postgres:password@postgres:5432/agent_khu

# 외부 DB
DATABASE_URL=postgresql://user:pass@db.example.com:5432/agent_khu
```

**구성 요소**:
- `username`: DB 사용자명
- `password`: DB 비밀번호
- `host`: DB 호스트 (localhost, IP, 도메인)
- `port`: DB 포트 (기본값: 5432)
- `database`: DB 이름

---

### 서버 설정

#### HOST

서버 바인딩 주소입니다.

**기본값**: `0.0.0.0`

```env
# 모든 네트워크 인터페이스에서 접근 가능
HOST=0.0.0.0

# localhost만 허용
HOST=127.0.0.1

# 특정 IP만 허용
HOST=192.168.1.100
```

**권장**:
- 개발: `127.0.0.1` (로컬만)
- 프로덕션: `0.0.0.0` (모든 IP)

---

#### PORT

서버 포트입니다.

**기본값**: `8000`

```env
PORT=8000
```

**주의사항**:
- 1024 미만 포트는 root 권한 필요
- 다른 서비스와 충돌 확인

---

### CORS 설정

#### CORS_ALLOW_ORIGINS

허용할 Origin 목록입니다 (쉼표로 구분).

**형식**:
```env
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:3000
```

**개발 환경**:
```env
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173
```

**프로덕션 환경**:
```env
CORS_ALLOW_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

**와일드카드 (비권장)**:
```env
CORS_ALLOW_ORIGINS=*
```
⚠️ 보안 위험: 모든 도메인 허용

---

### JWT 인증

#### JWT_SECRET_KEY

JWT 토큰 서명에 사용되는 비밀 키입니다.

**기본값**: `your-secret-key-change-this-in-production`

```env
JWT_SECRET_KEY=very-long-random-string-keep-it-secret
```

**생성 방법**:
```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32
```

**주의사항**:
- 최소 32자 이상 권장
- 무작위 문자열 사용
- 절대 공개하지 마세요
- 프로덕션에서 반드시 변경

---

#### ALGORITHM

JWT 알고리즘입니다.

**기본값**: `HS256`

```env
ALGORITHM=HS256
```

**지원 알고리즘**:
- `HS256`: HMAC with SHA-256 (권장)
- `HS384`: HMAC with SHA-384
- `HS512`: HMAC with SHA-512

---

#### ACCESS_TOKEN_EXPIRE_MINUTES

토큰 만료 시간입니다 (분 단위).

**기본값**: `60`

```env
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

**권장값**:
- 개발: `1440` (24시간)
- 프로덕션: `60` (1시간)
- 보안 중요: `15` (15분)

---

### MCP 설정

#### MCP_AUTOSTART

MCP 서버 자동 시작 여부입니다.

**기본값**: `true`

```env
MCP_AUTOSTART=true   # 자동 시작
MCP_AUTOSTART=false  # 수동 시작
```

**true**: FastAPI 시작 시 모든 MCP 서버 자동 시작
**false**: 첫 호출 시 Lazy start

---

#### MCP_INIT_TIMEOUT

MCP 서버 초기화 타임아웃입니다 (초).

**기본값**: `10`

```env
MCP_INIT_TIMEOUT=10
```

**권장값**:
- 빠른 서버: `5`
- 크롤링 서버: `15`
- 느린 네트워크: `30`

---

#### MCP_CALL_TIMEOUT

MCP Tool 호출 타임아웃입니다 (초).

**기본값**: `60`

```env
MCP_CALL_TIMEOUT=60
```

**권장값**:
- 간단한 조회: `10`
- 크롤링: `60`
- 복잡한 작업: `120`

---

#### MCP_ROOT

MCP 서버 디렉토리 경로입니다.

**기본값**: 자동 감지

```env
MCP_ROOT=/path/to/agent-khu/mcp-servers
```

**자동 감지 순서**:
1. 환경변수 `MCP_ROOT`
2. 프로젝트 루트 기준 `../mcp-servers`
3. 실행 위치 기준 `../mcp-servers`
4. 홈 디렉토리 `~/Desktop/agent-khu/mcp-servers`

---

### 로깅

#### LOG_LEVEL

로그 레벨입니다.

**기본값**: `INFO`

```env
LOG_LEVEL=DEBUG
```

**레벨**:
- `DEBUG`: 모든 로그 (개발용)
- `INFO`: 일반 정보 (기본값)
- `WARNING`: 경고만
- `ERROR`: 에러만
- `CRITICAL`: 치명적 에러만

---

#### DEBUG

디버그 모드입니다.

**기본값**: `false`

```env
DEBUG=true   # 개발 환경
DEBUG=false  # 프로덕션 환경
```

**true일 때**:
- 상세한 에러 메시지
- 스택 트레이스 노출
- Auto-reload

---

## Frontend 환경변수

### VITE_API_URL

Backend API URL입니다.

**형식**:
```env
VITE_API_URL=http://localhost:8000
```

**개발 환경**:
```env
VITE_API_URL=http://localhost:8000
```

**프로덕션 환경**:
```env
VITE_API_URL=https://api.yourdomain.com
```

**주의사항**:
- Vite 환경변수는 `VITE_` 접두사 필수
- 변경 후 `npm run dev` 재시작 필요
- 빌드 시 환경변수가 코드에 하드코딩됨

---

## 개발/프로덕션 설정

### 개발 환경

**backend/.env**
```env
# API
ANTHROPIC_API_KEY=sk-ant-your-dev-key

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/agent_khu

# Server
HOST=127.0.0.1
PORT=8000

# CORS
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:3000

# JWT
JWT_SECRET_KEY=dev-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# MCP
MCP_AUTOSTART=true
MCP_INIT_TIMEOUT=10
MCP_CALL_TIMEOUT=60

# Logging
LOG_LEVEL=DEBUG
DEBUG=true
```

**frontend/.env**
```env
VITE_API_URL=http://localhost:8000
```

---

### 프로덕션 환경

**backend/.env**
```env
# API
ANTHROPIC_API_KEY=sk-ant-your-production-key

# Database
DATABASE_URL=postgresql://user:strong-password@db.example.com:5432/agent_khu

# Server
HOST=0.0.0.0
PORT=8000

# CORS
CORS_ALLOW_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# JWT
JWT_SECRET_KEY=very-long-random-production-secret-key-32-chars-minimum
ACCESS_TOKEN_EXPIRE_MINUTES=60

# MCP
MCP_AUTOSTART=true
MCP_INIT_TIMEOUT=15
MCP_CALL_TIMEOUT=120

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

**frontend/.env**
```env
VITE_API_URL=https://api.yourdomain.com
```

---

## 보안 권장사항

### 1. API 키 보호

```bash
# ✅ 좋은 예: 환경변수
export ANTHROPIC_API_KEY=sk-ant-...

# ❌ 나쁜 예: 코드에 하드코딩
api_key = "sk-ant-..."
```

### 2. .env 파일 Git 제외

```bash
# .gitignore
.env
*.env
**/.env
!.env.example
```

### 3. JWT Secret 생성

```bash
# 강력한 랜덤 문자열 생성
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. 비밀번호 강도

```env
# ❌ 약한 비밀번호
DATABASE_URL=postgresql://postgres:password@...

# ✅ 강한 비밀번호
DATABASE_URL=postgresql://postgres:Xk9$mN2#pQw7@...
```

### 5. CORS 제한

```env
# ❌ 모든 도메인 허용 (위험)
CORS_ALLOW_ORIGINS=*

# ✅ 특정 도메인만 허용
CORS_ALLOW_ORIGINS=https://yourdomain.com
```

### 6. 환경변수 검증

```bash
# 민감한 환경변수 확인
echo $ANTHROPIC_API_KEY | grep -o "sk-ant-.*"

# .env 파일이 Git에 없는지 확인
git ls-files | grep .env
```

---

## 환경변수 로드 순서

### Backend (Python)

```python
# 1. 시스템 환경변수
import os
api_key = os.getenv("ANTHROPIC_API_KEY")

# 2. .env 파일 (python-dotenv)
from dotenv import load_dotenv
load_dotenv()

# 3. 기본값
api_key = os.getenv("ANTHROPIC_API_KEY", "default-value")
```

### Frontend (Vite)

```typescript
// 1. 빌드 시 환경변수 (.env 파일)
const apiUrl = import.meta.env.VITE_API_URL;

// 2. 런타임 환경변수 (지원 안 됨)
// Vite는 빌드 시 환경변수를 코드에 삽입
```

---

## 문제 해결

### 환경변수가 적용되지 않음

```bash
# 1. 파일 존재 확인
ls -la backend/.env

# 2. 내용 확인
cat backend/.env

# 3. 서버 재시작
# Backend
uvicorn app.main:app --reload

# Frontend
npm run dev
```

### .env 파일 형식 오류

```env
# ❌ 잘못된 형식
ANTHROPIC_API_KEY = sk-ant-...  # 공백 주의
CORS_ALLOW_ORIGINS="http://localhost:5173"  # 따옴표 불필요

# ✅ 올바른 형식
ANTHROPIC_API_KEY=sk-ant-...
CORS_ALLOW_ORIGINS=http://localhost:5173
```

### Docker Compose 환경변수

```yaml
# docker-compose.yml
services:
  backend:
    env_file:
      - ./backend/.env
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/agent_khu
```

**우선순위**: `environment` > `env_file` > `.env`

---

## 참고 자료

- [python-dotenv 문서](https://github.com/theskumar/python-dotenv)
- [Vite 환경변수](https://vitejs.dev/guide/env-and-mode.html)
- [FastAPI 설정](https://fastapi.tiangolo.com/advanced/settings/)