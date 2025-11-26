# MCP 서버 개발 가이드 🔌

새로운 MCP 서버를 추가하는 방법을 설명합니다.

---

## 📋 목차

- [MCP 프로토콜 개요](#mcp-프로토콜-개요)
- [서버 구조](#서버-구조)
- [개발 단계](#개발-단계)
- [JSON-RPC 2.0 표준](#json-rpc-20-표준)
- [테스트](#테스트)
- [배포](#배포)

---

## MCP 프로토콜 개요

### Model Context Protocol (MCP)

MCP는 AI 모델과 외부 도구를 연결하는 **표준 프로토콜**입니다.

**핵심 개념**:
- **stdio 통신**: 표준 입출력으로 JSON-RPC 메시지 교환
- **Tool 기반**: 각 서버는 여러 Tool 제공
- **Stateless**: 각 요청은 독립적

### 통신 흐름

```
┌──────────┐         JSON-RPC          ┌──────────┐
│  Client  │ ───────────────────────>  │  Server  │
│          │       (stdin)             │          │
│          │ <───────────────────────  │          │
│          │       (stdout)            │          │
└──────────┘                           └──────────┘
```

---

## 서버 구조

### 필수 구성 요소

```
my-mcp/
├── server.py                # 메인 서버 (필수)
├── README.md                # 문서 (권장)
├── requirements.txt         # Python 의존성 (선택)
├── scrapers/                # 크롤링 로직 (선택)
│   └── my_scraper.py
└── data/                    # 캐시/데이터 (선택)
    └── cache.json
```

### server.py 템플릿

```python
"""
My MCP Server
설명을 여기에 작성
"""
import asyncio
import json
import sys
from typing import Any, Dict

# ============================================
# MCP 표준 함수
# ============================================

def _readline():
    """stdin에서 한 줄 읽기"""
    line = sys.stdin.readline()
    if not line:
        return None
    try:
        return json.loads(line.strip())
    except json.JSONDecodeError:
        return None

def _send(obj: dict):
    """stdout으로 JSON 전송"""
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def _result(id_: int, data: Any, is_error: bool = False):
    """표준 result 응답 생성"""
    content = [{
        "type": "text",
        "text": json.dumps(data, ensure_ascii=False, indent=2)
    }]
    res = {
        "jsonrpc": "2.0",
        "id": id_,
        "result": {
            "content": content,
            "isError": is_error
        }
    }
    _send(res)

# ============================================
# Tools 구현
# ============================================

async def tool_my_tool(args: Dict) -> Dict:
    """
    Tool 설명
    
    Args:
        args: {
            "param1": "값1",
            "param2": "값2"
        }
    
    Returns:
        결과 딕셔너리
    """
    param1 = args.get("param1", "")
    param2 = args.get("param2", "")
    
    # 로직 구현
    result = {
        "success": True,
        "data": {
            "param1": param1,
            "param2": param2
        }
    }
    
    return result

# ============================================
# 메인 루프
# ============================================

async def main():
    # Tool 등록
    tools = {
        "my_tool": tool_my_tool,
    }
    
    while True:
        msg = _readline()
        if msg is None:
            break
        
        # 1. initialize
        if msg.get("method") == "initialize":
            _send({
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "my-mcp",
                        "version": "1.0.0"
                    }
                }
            })
            continue
        
        # 2. notifications/initialized
        if msg.get("method") == "notifications/initialized":
            continue
        
        # 3. tools/list
        if msg.get("method") == "tools/list":
            _send({
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "my_tool",
                            "description": "Tool 설명",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "param1": {
                                        "type": "string",
                                        "description": "파라미터 1 설명"
                                    },
                                    "param2": {
                                        "type": "string",
                                        "description": "파라미터 2 설명"
                                    }
                                },
                                "required": ["param1"]
                            }
                        }
                    ]
                }
            })
            continue
        
        # 4. tools/call
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
        
        # 5. 기타
        if "id" in msg:
            _result(msg["id"], {"status": "noop"})

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 개발 단계

### 1. 디렉토리 생성

```bash
cd ~/Desktop/agent-khu/mcp-servers
mkdir my-mcp
cd my-mcp
```

### 2. server.py 작성

위 템플릿을 복사하여 작성합니다.

**주요 수정 사항**:
- `tool_my_tool` 함수 구현
- `tools` 딕셔너리에 Tool 등록
- `tools/list`에 Tool 메타데이터 추가

### 3. 로컬 테스트

```bash
# 초기화 테스트
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python server.py

# Tool 호출 테스트
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"my_tool","arguments":{"param1":"test"}}}' | python server.py
```

### 4. mcp_client.py 등록

**파일**: `backend/app/mcp_client.py`

```python
def _register_default_servers(self) -> None:
    paths = {
        # 기존 서버들...
        "my_mcp": self.mcp_dir / "my-mcp/server.py",
    }
    self.server_paths.update(paths)
```

### 5. agent.py에 Tool 추가

**파일**: `backend/app/agent.py`

```python
tools = [
    # 기존 Tools...
    {
        "name": "my_tool",
        "description": "Tool 설명 (Claude가 이해할 수 있게 명확히)",
        "input_schema": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "파라미터 설명"
                }
            },
            "required": ["param1"]
        }
    },
]
```

**Tool 처리 로직 추가**:

```python
async def process_tool_call(tool_name: str, tool_input: Dict, db: Session) -> Dict:
    # 기존 처리...
    
    # 새 Tool 추가
    elif tool_name == "my_tool":
        result = await mcp_client.call_tool("my_mcp", "my_tool", tool_input)
        accumulated_results["my_tool_data"].append(result)
        return result
```

### 6. 통합 테스트

```bash
# Backend 재시작
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Frontend에서 테스트
"my_tool을 사용해서 param1이 test인 결과를 보여줘"
```

---

## JSON-RPC 2.0 표준

### 요청 형식

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "my_tool",
    "arguments": {
      "param1": "value1"
    }
  }
}
```

### 응답 형식 (성공)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"success\": true, \"data\": {...}}"
      }
    ],
    "isError": false
  }
}
```

### 응답 형식 (에러)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"error\": \"Error message\"}"
      }
    ],
    "isError": true
  }
}
```

### 필수 메서드

| 메서드 | 설명 | 응답 |
|--------|------|------|
| `initialize` | 서버 초기화 | capabilities |
| `notifications/initialized` | 초기화 완료 알림 | 없음 |
| `tools/list` | Tool 목록 조회 | tools 배열 |
| `tools/call` | Tool 호출 | result |

---

## 테스트

### 단위 테스트

```python
# test_my_mcp.py
import asyncio
from server import tool_my_tool

async def test_my_tool():
    result = await tool_my_tool({"param1": "test"})
    assert result["success"] == True
    assert "data" in result
    print("✅ 테스트 통과")

if __name__ == "__main__":
    asyncio.run(test_my_tool())
```

### JSON-RPC 테스트

```bash
# test_jsonrpc.sh
#!/bin/bash

echo "1. Initialize"
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python server.py

echo "2. Tools List"
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | python server.py

echo "3. Call Tool"
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"my_tool","arguments":{"param1":"test"}}}' | python server.py
```

### 통합 테스트

```python
# test_integration.py
import asyncio
from app.mcp_client import MCPClient

async def test():
    client = MCPClient()
    await client.start_server("my_mcp", "path/to/my-mcp/server.py")
    
    result = await client.call_tool("my_mcp", "my_tool", {
        "param1": "test"
    })
    
    print(result)
    assert result["success"] == True

if __name__ == "__main__":
    asyncio.run(test())
```

---

## 베스트 프랙티스

### 1. 에러 처리

```python
async def tool_my_tool(args: Dict) -> Dict:
    try:
        param1 = args.get("param1")
        if not param1:
            return {
                "success": False,
                "error": "param1이 필요합니다"
            }
        
        # 로직...
        return {"success": True, "data": {...}}
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

### 2. 로깅

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def tool_my_tool(args: Dict) -> Dict:
    logger.info(f"my_tool 호출: {args}")
    # 로직...
    logger.info(f"my_tool 완료: {result}")
    return result
```

### 3. 캐싱

```python
import json
from pathlib import Path

CACHE_PATH = Path(__file__).parent / "data/cache.json"

def load_cache():
    if CACHE_PATH.exists():
        with open(CACHE_PATH) as f:
            return json.load(f)
    return {}

def save_cache(data):
    CACHE_PATH.parent.mkdir(exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

### 4. 타임아웃

```python
import asyncio

async def tool_with_timeout(args: Dict) -> Dict:
    try:
        result = await asyncio.wait_for(
            long_running_task(args),
            timeout=30.0  # 30초
        )
        return result
    except asyncio.TimeoutError:
        return {
            "success": False,
            "error": "타임아웃 (30초 초과)"
        }
```

---

## 배포

### 1. README.md 작성

```markdown
# My MCP Server

설명...

## 기능
- ...

## Tools
### my_tool
- 입력: ...
- 출력: ...

## 사용법
\`\`\`bash
python server.py
\`\`\`
```

### 2. requirements.txt

```txt
requests==2.31.0
lxml==5.1.0
```

### 3. Git 커밋

```bash
git add mcp-servers/my-mcp/
git commit -m "feat(mcp): add my-mcp server"
git push
```

---

## 예제 MCP 서버

### 간단한 계산기 MCP

```python
async def tool_calculate(args: Dict) -> Dict:
    """사칙연산 계산"""
    operation = args.get("operation")  # add, sub, mul, div
    a = args.get("a", 0)
    b = args.get("b", 0)
    
    operations = {
        "add": lambda x, y: x + y,
        "sub": lambda x, y: x - y,
        "mul": lambda x, y: x * y,
        "div": lambda x, y: x / y if y != 0 else None
    }
    
    if operation not in operations:
        return {"error": "지원하지 않는 연산"}
    
    result = operations[operation](a, b)
    if result is None:
        return {"error": "0으로 나눌 수 없습니다"}
    
    return {
        "operation": operation,
        "a": a,
        "b": b,
        "result": result
    }
```

---

## 참고 자료

- [Model Context Protocol 공식 문서](https://modelcontextprotocol.io/)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [curriculum-mcp 소스 코드](../mcp-servers/curriculum-mcp/)
- [notice-mcp 소스 코드](../mcp-servers/notice-mcp/)

---

## 도움말

문제가 있거나 질문이 있다면:
- [GitHub Issues](https://github.com/jys0615/agent-khu/issues)
- [문제 해결 가이드](TROUBLESHOOTING.md)