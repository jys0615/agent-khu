# Contributing to Agent KHU

Agent KHU에 관심 가져주셔서 감사합니다! 이 문서는 프로젝트에 기여하는 방법을 안내합니다.

---

## 📋 목차

- [행동 강령](#행동-강령)
- [기여 방법](#기여-방법)
- [개발 환경 설정](#개발-환경-설정)
- [코드 스타일](#코드-스타일)
- [커밋 메시지](#커밋-메시지)
- [Pull Request 가이드](#pull-request-가이드)
- [이슈 제보](#이슈-제보)

---

## 행동 강령

이 프로젝트는 [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md)를 따릅니다. 참여함으로써 이 강령을 준수하는 데 동의하는 것으로 간주됩니다.

---

## 기여 방법

### 🐛 버그 리포트
버그를 발견하셨나요? [이슈를 생성](https://github.com/jys0615/agent-khu/issues/new?template=bug_report.md)해주세요.

### ✨ 기능 제안
새로운 기능 아이디어가 있나요? [기능 제안 이슈](https://github.com/jys0615/agent-khu/issues/new?template=feature_request.md)를 생성해주세요.

### 📖 문서 개선
오타나 설명이 부족한 부분을 발견하셨나요? 문서 개선도 큰 기여입니다!

### 🔧 코드 기여
1. Fork & Clone
2. 브랜치 생성
3. 개발 & 테스트
4. Pull Request

---

## 개발 환경 설정

### 1. 저장소 Fork & Clone

```bash
# Fork 후
git clone https://github.com/jys0615/agent-khu.git
cd agent-khu

# Upstream 추가
git remote add upstream https://github.com/ORIGINAL_OWNER/agent-khu.git
```

### 2. 의존성 설치

**Backend**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend**
```bash
cd frontend
npm install
```

### 3. 환경변수 설정

```bash
# Backend
cp backend/.env.example backend/.env
# .env 파일 편집 (ANTHROPIC_API_KEY 등)

# Frontend
cp frontend/.env.example frontend/.env
```

### 4. 데이터베이스 초기화

```bash
# Docker Compose 사용
docker-compose up -d postgres

# 테이블 생성
cd backend
python init_db.py
```

### 5. 개발 서버 실행

**Backend**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm run dev
```

---

## 개발 권장사항

### Frontend 폼 개발
로그인/회원가입 등의 폼을 개발할 때는 다음 사항을 준수해주세요:

**브라우저 Credential 지원**
- 폼에 `autoComplete` 속성 추가 (`autoComplete="on"`)
- 입력 필드에 적절한 `name`과 `autoComplete` 값 설정
  - 아이디: `name="username"`, `autoComplete="username"`
  - 비밀번호 (로그인): `autoComplete="current-password"`
  - 비밀번호 (회원가입): `autoComplete="new-password"`
  - 이메일: `autoComplete="email"`

**예시**:
```tsx
<form autoComplete="on">
  <input
    name="username"
    autoComplete="username"
    // ...
  />
  <input
    name="password"
    type="password"
    autoComplete="current-password"
    // ...
  />
</form>
```

---

## 코드 스타일

### Python (Backend)

**PEP 8 준수**
```bash
# 포매터 (자동 수정)
black backend/

# 린터 (검사)
flake8 backend/
```

**주요 규칙**
- 들여쓰기: 4 스페이스
- 최대 줄 길이: 88자 (Black 기본값)
- Import 순서: 표준 라이브러리 → 서드파티 → 로컬
- Docstring: Google 스타일

**예시**
```python
def search_classroom(query: str, limit: int = 5) -> List[Dict]:
    """강의실을 검색합니다.

    Args:
        query: 검색어
        limit: 최대 결과 수

    Returns:
        검색 결과 리스트

    Raises:
        ValueError: 검색어가 비어있을 때
    """
    if not query:
        raise ValueError("검색어를 입력해주세요")
    
    # 구현...
    return results
```

### TypeScript (Frontend)

**Prettier + ESLint**
```bash
# 포매터
npm run format

# 린터
npm run lint
```

**주요 규칙**
- 들여쓰기: 4 스페이스
- 세미콜론: 사용
- 따옴표: 작은따옴표 (')
- 타입 명시: 모든 함수/변수

**예시**
```typescript
interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

async function sendMessage(message: string): Promise<ChatMessage> {
    const response = await api.post('/chat', { message });
    return response.data;
}
```

### MCP Server (Python/TypeScript)

**JSON-RPC 2.0 표준 준수**
```python
# 필수 구조
def _readline():
    """stdin에서 JSON-RPC 메시지 읽기"""
    pass

def _send(obj: dict):
    """JSON-RPC 응답 전송"""
    pass

def _result(id_: int, data: Any, is_error: bool = False):
    """표준 result 형식으로 응답"""
    pass
```

---

## 커밋 메시지

### Conventional Commits 형식

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**
- `feat`: 새 기능
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 포매팅 (기능 변경 없음)
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드/설정 변경

**Scope** (선택)
- `backend`: 백엔드
- `frontend`: 프론트엔드
- `mcp`: MCP 서버
- `docs`: 문서
- `ci`: CI/CD

**예시**
```bash
feat(mcp): add curriculum-mcp server with rowspan handling

- Implement rowspan detection for course tables
- Add 24-hour auto-update mechanism
- Add SHA256 hash-based change detection

Closes #123
```

```bash
fix(backend): resolve JWT token expiration issue

- Increase token lifetime to 1 hour
- Add token refresh endpoint

Fixes #456
```

---

## Pull Request 가이드

### 1. 브랜치 생성

```bash
# 최신 상태로 업데이트
git checkout main
git pull upstream main

# 기능 브랜치 생성
git checkout -b feature/your-feature-name
# 또는
git checkout -b fix/bug-description
```

### 2. 개발 & 테스트

```bash
# 코드 작성
# 테스트 실행
pytest backend/tests/
npm test  # frontend

# 포매팅
black backend/
npm run format
```

### 3. 커밋 & 푸시

```bash
git add .
git commit -m "feat(mcp): add new feature"
git push origin feature/your-feature-name
```

### 4. Pull Request 생성

GitHub에서 PR 생성 시 다음 사항을 포함해주세요:

**PR 제목**
```
feat(mcp): add shuttle-mcp real-time tracking
```

**PR 설명**
```markdown
## 변경 사항
- 셔틀버스 실시간 위치 추적 기능 추가
- GPS 좌표 기반 도착 시간 예측
- WebSocket 연결로 실시간 업데이트

## 동기
#123 이슈에서 요청된 기능

## 테스트
- [x] 단위 테스트 작성
- [x] 수동 테스트 완료
- [ ] E2E 테스트 (TODO)

## 스크린샷
(해당되는 경우 첨부)

## 체크리스트
- [x] 코드 포매팅 완료
- [x] 문서 업데이트
- [x] CHANGELOG.md 업데이트
- [x] 테스트 통과
```

### 5. 코드 리뷰

- 리뷰어의 피드백에 응답
- 요청된 변경사항 수정
- `git push origin feature/your-feature-name` (자동 반영)

---

## 이슈 제보

### 버그 리포트

**좋은 버그 리포트에는 다음이 포함됩니다:**

1. **명확한 제목**: "curriculum-mcp: rowspan parsing error for row 2"
2. **환경 정보**: OS, Python 버전, 브라우저 등
3. **재현 단계**: 순서대로 명확하게
4. **예상 동작**: 어떻게 작동해야 하는지
5. **실제 동작**: 무엇이 잘못되었는지
6. **로그/스크린샷**: 에러 메시지, 스택 트레이스

**템플릿**
```markdown
### 환경
- OS: macOS 14.0
- Python: 3.9.7
- Browser: Chrome 120

### 재현 단계
1. curriculum-mcp 서버 시작
2. "자료구조" 검색
3. 결과 확인

### 예상 동작
```json
{
  "code": "CSE204",
  "name": "자료구조",
  "credits": 3
}
```

### 실제 동작
```json
{
  "code": "CSE204",
  "name": "3",
  "credits": 2
}
```

### 추가 정보
- rowspan 속성으로 인한 컬럼 shift 문제로 추정
- [에러 로그 첨부]
```

### 기능 제안

**좋은 기능 제안에는 다음이 포함됩니다:**

1. **문제 설명**: 현재 어떤 불편함이 있는지
2. **제안 내용**: 어떤 기능을 추가하고 싶은지
3. **대안**: 다른 해결 방법은 없는지
4. **추가 정보**: 관련 자료, 예시 등

**예시**
```markdown
### 문제
현재 도서관 좌석 조회는 로그인이 필수입니다.
로그인 없이도 대략적인 좌석 현황을 보고 싶습니다.

### 제안
- 로그인 없이 열람실별 전체 좌석 수 표시
- 로그인하면 실시간 상세 현황 표시

### 대안
- 공개 API가 있다면 활용
- 없다면 주기적 크롤링

### 참고
다른 대학 도서관 앱 예시: ...
```

---

## MCP 서버 추가 가이드

새로운 MCP 서버를 추가하려면:

### 1. 디렉토리 생성

```bash
mkdir mcp-servers/your-mcp
cd mcp-servers/your-mcp
```

### 2. server.py 작성

```python
"""
Your MCP Server
"""
import asyncio
import json
import sys
from typing import Any, Dict

# MCP 표준 함수
def _readline():
    line = sys.stdin.readline()
    if not line:
        return None
    try:
        return json.loads(line.strip())
    except Exception:
        return None

def _send(obj: dict):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def _result(id_: int, data: Any, is_error: bool = False):
    content = [{"type": "text", "text": json.dumps(data, ensure_ascii=False, indent=2)}]
    res = {
        "jsonrpc": "2.0",
        "id": id_,
        "result": {"content": content, "isError": is_error}
    }
    _send(res)

# Tools
async def tool_your_tool(args: Dict) -> Dict:
    """Your tool implementation"""
    # 구현...
    return {"result": "success"}

# MCP 메인 루프
async def main():
    tools = {
        "your_tool": tool_your_tool,
    }
    
    while True:
        msg = _readline()
        if msg is None:
            break
        
        # initialize
        if msg.get("method") == "initialize":
            _send({
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}}
                }
            })
            continue
        
        # notifications/initialized
        if msg.get("method") == "notifications/initialized":
            continue
        
        # tools/list
        if msg.get("method") == "tools/list":
            _send({
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "your_tool",
                            "description": "Tool description",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "param": {"type": "string"}
                                },
                                "required": ["param"]
                            }
                        }
                    ]
                }
            })
            continue
        
        # tools/call
        if msg.get("method") == "tools/call":
            req_id = msg.get("id")
            params = msg.get("params", {})
            name = params.get("name")
            arguments = params.get("arguments", {})
            
            if name not in tools:
                _result(req_id, {"error": f"Unknown tool: {name}"}, is_error=True)
                continue
            
            try:
                result = await tools[name](arguments)
                _result(req_id, result)
            except Exception as e:
                _result(req_id, {"error": str(e)}, is_error=True)
            continue
        
        # 기타
        if "id" in msg:
            _result(msg["id"], {"status": "noop"})

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. README.md 작성

```markdown
# Your MCP Server

설명...

## 기능
- ...

## 사용법
\`\`\`bash
python server.py
\`\`\`

## Tools
### your_tool
- 설명: ...
- 입력: ...
- 출력: ...
```

### 4. mcp_client.py 등록

```python
# backend/app/mcp_client.py
def _register_default_servers(self) -> None:
    paths = {
        # ...
        "your_mcp": self.mcp_dir / "your-mcp/server.py",
    }
    self.server_paths.update(paths)
```

### 5. agent.py에 Tool 추가

```python
# backend/app/agent.py
tools = [
    # ...
    {
        "name": "your_tool",
        "description": "...",
        "input_schema": {...}
    },
]
```

### 6. 테스트

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python server.py
```

자세한 내용은 [MCP 서버 개발 가이드](https://github.com/jys0615/agent-khu/blob/main/docs/MCP_SERVERS.md) 참고

---

## 질문하기

질문이 있으시면:
- 📖 [문서](https://github.com/jys0615/agent-khu/tree/main/docs)를 먼저 확인해주세요
- 💬 [Discussions](https://github.com/jys0615/agent-khu/discussions)에서 질문
- 🐛 버그라면 [Issue](https://github.com/jys0615/agent-khu/issues) 생성

---

## 감사합니다! 🙏

기여해주셔서 감사합니다. 모든 기여는 프로젝트를 더 나은 방향으로 발전시킵니다!