"""
MCP 클라이언트 - 영구 세션 풀 (Phase 1 리팩토링)

Before: call_tool() 호출마다 subprocess spawn + initialize(12s) + 종료
After : 앱 startup에 1회 세션 생성 → 이후 모든 호출에서 재사용
        실패 시 자동 재연결 1회 재시도 (_reconnect_lock으로 경합 방지)
"""
from __future__ import annotations

import os
import sys
import asyncio
import logging
from contextlib import AsyncExitStack
from typing import Dict, Any, Optional
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

log = logging.getLogger(__name__)


class MCPServerSession:
    """개별 MCP 서버와의 영구 세션"""

    def __init__(self, name: str, params: StdioServerParameters) -> None:
        self.name = name
        self.params = params
        self._session: Optional[ClientSession] = None
        self._exit_stack = AsyncExitStack()
        self._reconnect_lock = asyncio.Lock()

    async def start(self) -> None:
        read, write = await self._exit_stack.enter_async_context(
            stdio_client(self.params)
        )
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await asyncio.wait_for(self._session.initialize(), timeout=15.0)
        log.info("MCP 세션 시작: %s", self.name)

    async def stop(self) -> None:
        try:
            await self._exit_stack.aclose()
        except Exception as e:
            log.debug("MCP 세션 종료 중 오류 (%s): %s", self.name, e)
        finally:
            self._exit_stack = AsyncExitStack()
            self._session = None
        log.info("MCP 세션 종료: %s", self.name)

    async def call_tool(self, tool_name: str, arguments: dict, timeout: float) -> Any:
        # 세션 없으면 lazy start (startup 실패 서버 대비)
        if self._session is None:
            async with self._reconnect_lock:
                if self._session is None:
                    await self.start()

        try:
            return await asyncio.wait_for(
                self._session.call_tool(tool_name, arguments),
                timeout=timeout,
            )
        except Exception as e:
            log.warning("MCP tool 실패, 재연결 시도 (%s.%s): %s", self.name, tool_name, e)
            async with self._reconnect_lock:
                await self.stop()
                await self.start()
            return await asyncio.wait_for(
                self._session.call_tool(tool_name, arguments),
                timeout=timeout,
            )


class MCPClient:
    """영구 세션 풀 기반 MCP 클라이언트"""

    def __init__(self) -> None:
        self.server_paths: Dict[str, Path] = {}
        self.server_params: Dict[str, StdioServerParameters] = {}
        self._sessions: Dict[str, MCPServerSession] = {}

        env_root = os.getenv("MCP_ROOT")
        candidates = []

        if env_root:
            p = Path(env_root)
            if p.exists():
                candidates.append(p)

        try:
            repo_root = Path(__file__).resolve().parents[2]
            candidates.append(repo_root / "mcp-servers")
        except Exception:
            pass

        try:
            cwd = Path(os.getcwd()).resolve()
            candidates.append((cwd / "../mcp-servers").resolve())
            candidates.append(cwd / "mcp-servers")
        except Exception:
            pass

        candidates.append(Path.home() / "Desktop/agent-khu/mcp-servers")

        root: Optional[Path] = None
        for c in candidates:
            try:
                if c.exists():
                    root = c.resolve()
                    break
            except Exception:
                continue

        if root is None:
            root = candidates[-1]
            log.warning("MCP 디렉터리를 찾지 못했습니다: %s", root)

        self.mcp_dir = root
        log.debug("MCP_DIR = %s", self.mcp_dir)

        self._register_default_servers()

    def _register_default_servers(self) -> None:
        paths = {
            "classroom": self.mcp_dir / "classroom-mcp/server.py",
            "notice":    self.mcp_dir / "notice-mcp/server.py",
            "meal":      self.mcp_dir / "meal-mcp/server.py",
            "library":   self.mcp_dir / "library-mcp/server.py",
            "course":    self.mcp_dir / "course-mcp/server.py",
            "curriculum": self.mcp_dir / "curriculum-mcp/server.py",
        }
        self.server_paths.update(paths)

        env = os.environ.copy()
        try:
            backend_root = Path(__file__).resolve().parents[1]
            existing_pp = env.get("PYTHONPATH", "")
            pp_parts = [p for p in existing_pp.split(os.pathsep) if p]
            if str(backend_root) not in pp_parts:
                pp_parts.append(str(backend_root))
            env["PYTHONPATH"] = os.pathsep.join(pp_parts) if pp_parts else str(backend_root)
            env.setdefault("PYTHONUNBUFFERED", "1")
        except Exception:
            pass

        python_cmd = sys.executable or "python3"

        for name, path in paths.items():
            if path.exists():
                self.server_params[name] = StdioServerParameters(
                    command=python_cmd,
                    args=[str(path)],
                    env=env,
                )
                self._sessions[name] = MCPServerSession(name, self.server_params[name])

    async def start_all(self) -> None:
        """앱 startup 시 모든 MCP 서버 세션을 동시에 시작"""
        results = await asyncio.gather(
            *[s.start() for s in self._sessions.values()],
            return_exceptions=True,
        )
        for name, result in zip(self._sessions.keys(), results):
            if isinstance(result, Exception):
                log.warning("MCP 세션 시작 실패 (%s): %s — lazy start로 대체", name, result)

    async def stop_all(self) -> None:
        """앱 shutdown 시 모든 세션 종료"""
        await asyncio.gather(
            *[s.stop() for s in self._sessions.values()],
            return_exceptions=True,
        )
        log.info("MCP Client 전체 종료 완료")

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        *,
        timeout: float = 10.0,
        retries: int = 1,  # API 호환성 유지 (내부 retry는 MCPServerSession에서 처리)
    ) -> Any:
        session = self._sessions.get(server_name)
        if not session:
            raise ValueError(f"등록되지 않은 MCP 서버: {server_name}")

        result = await session.call_tool(tool_name, arguments, timeout)
        return self._parse_result(result)

    def _parse_result(self, result: Any) -> Any:
        """MCP 결과 파싱"""
        if hasattr(result, 'content') and result.content:
            if isinstance(result.content, list):
                texts = []
                for item in result.content:
                    if hasattr(item, 'text'):
                        texts.append(item.text)
                    elif isinstance(item, dict) and 'text' in item:
                        texts.append(item['text'])
                if texts:
                    combined = "\n".join(texts)
                    try:
                        import json
                        return json.loads(combined)
                    except json.JSONDecodeError:
                        return combined
            if hasattr(result.content, 'text'):
                try:
                    import json
                    return json.loads(result.content.text)
                except json.JSONDecodeError:
                    return result.content.text
        return result

    # ── Convenience wrappers ──────────────────────────────────────────────────
    async def meal_get_today(self, meal_type: str = "lunch") -> Any:
        return await self.call_tool("meal", "get_today_meal", {"meal_type": meal_type})

    async def meal_scrape_weekly(self) -> Any:
        return await self.call_tool("meal", "scrape_weekly_meal", {})

    async def library_info(self, campus: str = "seoul") -> Any:
        return await self.call_tool("library", "get_library_info", {"campus": campus})

    async def library_seats(self, username: str, password: str, campus: str = "seoul") -> Any:
        return await self.call_tool("library", "get_seat_availability", {
            "username": username, "password": password, "campus": campus
        })

    async def library_reserve(self, username: str, password: str, room: str, seat_number: str | None = None) -> Any:
        payload = {"username": username, "password": password, "room": room}
        if seat_number:
            payload["seat_number"] = seat_number
        return await self.call_tool("library", "reserve_seat", payload)

    async def course_search(self, department: str = "소프트웨어융합학과", keyword: str | None = None) -> Any:
        payload = {"department": department}
        if keyword:
            payload["keyword"] = keyword
        return await self.call_tool("course", "search_courses", payload)

    async def course_professor(self, professor: str) -> Any:
        return await self.call_tool("course", "get_professor_courses", {"professor": professor})

    async def course_by_code(self, code: str) -> Any:
        return await self.call_tool("course", "get_course_by_code", {"code": code})


# 전역 인스턴스
mcp_client = MCPClient()
