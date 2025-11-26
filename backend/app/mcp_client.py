"""
MCP 클라이언트 - MCP Server들과 stdio 통신 (개선판)
- 경로 해상도: MCP_ROOT 환경변수 우선, 프로젝트 상대경로 폴백, 최종 홈 데스크톱 폴백
- 타임아웃: ENV로 조정 (MCP_INIT_TIMEOUT, MCP_CALL_TIMEOUT)
- 지연 기동(lazy start): call_tool 시 서버 미기동이면 자동 기동
- 응답 파싱 강화: 여러 content 아이템 결합, isError 처리, 알림 무시
- 요청/응답 매칭: id 기준으로 해당 응답까지 읽기
"""
from __future__ import annotations

import asyncio
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class MCPClient:
    """MCP Server와 통신하는 클라이언트"""

    def __init__(self) -> None:
        self.servers: Dict[str, dict] = {}
        self.server_paths: Dict[str, Path] = {}

        # 경로 해상도: (1) 유효한 MCP_ROOT (2) 프로젝트 루트 기준 (3) CWD 기준 (4) 데스크톱 폴백
        env_root = os.getenv("MCP_ROOT")
        candidates = []

        # 1) ENV 제공 경로가 존재하는 경우에만 후보에 추가
        if env_root:
            p = Path(env_root)
            if p.exists():
                candidates.append(p)
            else:
                print(f"⚠️ MCP_ROOT 경로가 존재하지 않습니다: {p}")

        # 2) 프로젝트 루트 기준: backend/app/ → 상위 2단계가 repo 루트 → mcp-servers
        try:
            repo_root = Path(__file__).resolve().parents[2]
            candidates.append(repo_root / "mcp-servers")
        except Exception:
            pass

        # 3) 실행 위치 기준(cwd): backend에서 실행 시 ../mcp-servers 가 일반적
        try:
            cwd = Path(os.getcwd()).resolve()
            candidates.append((cwd / "../mcp-servers").resolve())
            candidates.append(cwd / "mcp-servers")  # 혹시 cwd가 repo 루트인 경우
        except Exception:
            pass

        # 4) 개발기 편의 폴백(데스크톱)
        candidates.append(Path.home() / "Desktop/agent-khu/mcp-servers")

        root: Optional[Path] = None
        for c in candidates:
            try:
                if c.exists():
                    root = c.resolve()
                    break
            except Exception:
                continue

        # 최종 결정: 하나도 없으면 마지막 후보를 사용(경고만 출력)
        if root is None:
            root = candidates[-1]
            print(f"⚠️ MCP 디렉터리를 찾지 못했습니다. 임시 경로 사용: {root}")

        self.mcp_dir = root
        print(f"🔧 MCP_DIR = {self.mcp_dir}")

        # 타임아웃 (초)
        self.init_timeout: float = float(os.getenv("MCP_INIT_TIMEOUT", "10"))
        self.call_timeout: float = float(os.getenv("MCP_CALL_TIMEOUT", "60"))

        # 기본 서버 경로 등록
        self._register_default_servers()

    # --------------------------- 내부 유틸 ---------------------------
    def _register_default_servers(self) -> None:
        paths = {
            "classroom": self.mcp_dir / "classroom-mcp/server.py",
            "notice": self.mcp_dir / "notice-mcp/server.py",
            "meal": self.mcp_dir / "meal-mcp/server.py",
            "library": self.mcp_dir / "library-mcp/server.py",
            "library": self.mcp_dir / "library-mcp/server.py",
            "shuttle": self.mcp_dir / "shuttle-mcp/server.py",
            "course": self.mcp_dir / "course-mcp/server.py",
            "curriculum": self.mcp_dir / "curriculum-mcp/server.py",
        }
        self.server_paths.update(paths)

    def _server_exists(self, server_name: str) -> bool:
        p = self.server_paths.get(server_name)
        return bool(p and p.exists())

    async def _read_until_response(self, process: asyncio.subprocess.Process, request_id: int) -> dict:
        """요청 ID에 해당하는 응답이 나올 때까지 라인을 읽는다.
        알림(notifications/initialized 등)은 건너뛴다.
        """
        while True:
            line = await asyncio.wait_for(process.stdout.readline(), timeout=self.call_timeout)
            if not line:
                raise Exception("MCP 프로세스에서 응답이 없습니다.")
            raw = line.decode().strip()
            if not raw:
                continue
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                # 로그 라인일 수 있음 → 계속 읽기
                continue
            # JSON-RPC 응답이며 id가 일치하는 경우 반환
            if isinstance(msg, dict) and msg.get("id") == request_id:
                return msg
            # 알림/다른 요청에 대한 응답은 무시하고 계속 읽기

    def _parse_result_text(self, result: Any) -> Any:
        """MCP result에서 텍스트를 뽑아내거나 원본 반환.
        - 새 형식: { content: [ {type: 'text', text: '...'}, ... ], isError?: bool }
        - 구 형식: [ {type: 'text', text: '...'} ]
        여러 아이템이 있으면 텍스트를 공백으로 이어붙인다.
        isError가 True면 예외를 던진다.
        """
        # dict 형식 (새 형식)
        if isinstance(result, dict):
            if result.get("isError"):
                content = result.get("content", [])
                text = " ".join(item.get("text", "") for item in content if isinstance(item, dict))
                raise Exception(f"MCP tool error: {text or 'unknown error'}")
            content = result.get("content")
            if isinstance(content, list):
                texts = [item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"]
                if texts:
                    return "\n".join(texts)
            return result
        # list 형식 (구 형식)
        if isinstance(result, list):
            texts = [item.get("text", "") for item in result if isinstance(item, dict) and item.get("type") == "text"]
            if texts:
                return "\n".join(texts)
        return result

    # --------------------------- 프로세스 제어 ---------------------------
    async def start_server(self, server_name: str, server_path: str | Path):
        """MCP Server 프로세스 시작 및 초기화"""
        path = Path(server_path)
        if not path.exists():
            raise FileNotFoundError(f"MCP 서버 스크립트를 찾을 수 없습니다: {path}")

        process = await asyncio.create_subprocess_exec(
            "python3",
            str(path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # 1) initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "agent-khu", "version": "1.0"},
            },
        }
        assert process.stdin is not None
        process.stdin.write((json.dumps(init_request) + "\n").encode())
        await process.stdin.drain()

        try:
            init_response_line = await asyncio.wait_for(process.stdout.readline(), timeout=self.init_timeout)
            init_response = json.loads(init_response_line.decode())
            if "error" in init_response:
                raise Exception(f"MCP 초기화 실패: {init_response['error']}")
        except asyncio.TimeoutError:
            raise Exception(f"MCP '{server_name}' 초기화 타임아웃({self.init_timeout}s)")

        # 2) notifications/initialized
        initialized_notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        process.stdin.write((json.dumps(initialized_notif) + "\n").encode())
        await process.stdin.drain()
        await asyncio.sleep(0.05)

        # 저장
        self.servers[server_name] = {"process": process, "request_id": 1, "initialized": True}
        return process

    async def start_all_servers(self):
        """모든 MCP Server 시작(존재하는 것만)"""
        for name, path in self.server_paths.items():
            if path.exists():
                try:
                    await self.start_server(name, path)
                    print(f"✅ MCP '{name}' 시작 완료: {path}")
                except Exception as e:
                    print(f"❌ MCP '{name}' 시작 실패: {e}")
            else:
                print(f"⚠️  MCP '{name}' 파일 없음: {path}")
        print("🚀 모든 MCP Server 준비 완료")

    async def _ensure_server(self, server_name: str) -> None:
        """서버가 없으면 경로를 찾아 지연 기동"""
        if server_name in self.servers:
            return
        path = self.server_paths.get(server_name)
        if not path:
            raise ValueError(f"등록되지 않은 MCP 서버: {server_name}")
        if not path.exists():
            raise FileNotFoundError(f"MCP 서버 스크립트를 찾을 수 없습니다: {path}")
        await self.start_server(server_name, path)

    # --------------------------- 툴 호출 ---------------------------
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """MCP Tool 호출 (지연 기동 + 견고한 응답 파싱)"""
        await self._ensure_server(server_name)
        server = self.servers.get(server_name)
        if not server or not server.get("initialized"):
            raise ValueError(f"MCP Server '{server_name}' not initialized")

        process: asyncio.subprocess.Process = server["process"]
        server["request_id"] += 1
        request_id = server["request_id"]

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        try:
            assert process.stdin is not None
            process.stdin.write((json.dumps(request) + "\n").encode())
            await process.stdin.drain()

            # 요청 ID에 맞는 응답을 받을 때까지 읽기
            response = await self._read_until_response(process, request_id)

            if "error" in response:
                raise Exception(f"MCP error: {response['error']}")

            result = response.get("result")
            parsed = self._parse_result_text(result)
            return parsed

        except asyncio.TimeoutError:
            raise Exception(f"MCP Server '{server_name}' timeout ({self.call_timeout}s)")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON from MCP '{server_name}': {e}")

    async def stop_all_servers(self):
        """모든 MCP Server 종료"""
        for name, server in list(self.servers.items()):
            process: asyncio.subprocess.Process = server["process"]
            try:
                if process.stdin and not process.stdin.is_closing():
                    process.stdin.close()
                await asyncio.wait_for(process.wait(), timeout=2.0)
            except Exception:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=2.0)
                except Exception:
                    process.kill()
                    await process.wait()
            print(f"🛑 MCP Server '{name}' 종료")
        self.servers.clear()


mcp_client = MCPClient()