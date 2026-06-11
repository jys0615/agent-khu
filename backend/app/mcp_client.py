"""
MCP 클라이언트 — HTTP 기반 (Phase 2 리팩토링)

Before (Phase 1): 각 MCP 서버를 subprocess로 spawn → stdio transport
After  (Phase 2): 각 MCP 서버가 독립 HTTP 프로세스 → Streamable HTTP transport

변경 핵심:
  - subprocess 관리 제거 (cold start 0ms)
  - FastMCP Client로 HTTP 연결 (stateless, 서버당 독립 포트)
  - start_all() / stop_all() → health check만 수행 (인터페이스 호환 유지)
  - _parse_result() / discover_tools() / get_tools() 인터페이스 동일
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

from fastmcp import Client as FastMCPClient

log = logging.getLogger(__name__)


class MCPHTTPSession:
    """개별 MCP HTTP 서버와의 연결 관리 (subprocess 없음)"""

    def __init__(self, name: str, url: str) -> None:
        self.name = name
        self.url = url
        # 하위 호환: health check 시 True로 설정
        self._session: Optional[bool] = None

    async def check_health(self, timeout: float = 5.0) -> bool:
        """서버 가용성 확인 (list_tools 호출)"""
        try:
            async with FastMCPClient(self.url, timeout=timeout) as client:
                await client.list_tools()
            self._session = True
            return True
        except Exception as e:
            log.warning("MCP HTTP health check 실패 (%s): %s", self.name, e)
            self._session = None
            return False

    async def call_tool(self, tool_name: str, arguments: dict, timeout: float = 10.0) -> Any:
        try:
            async with FastMCPClient(self.url, timeout=timeout) as client:
                return await client.call_tool(tool_name, arguments)
        except Exception as e:
            log.warning("MCP HTTP tool 실패 (%s.%s): %s", self.name, tool_name, e)
            raise

    async def list_tools(self) -> list:
        async with FastMCPClient(self.url, init_timeout=5.0) as client:
            return await client.list_tools()


class MCPClient:
    """HTTP 기반 MCP 클라이언트 (Phase 2 — subprocess 완전 제거)"""

    def __init__(self) -> None:
        self._sessions: Dict[str, MCPHTTPSession] = {}
        self._discovered_tools: list[dict] = []

        # 하위 호환 (health endpoint에서 참조)
        self.server_params: Dict[str, dict] = {}

        self._setup_sessions()

    def _setup_sessions(self) -> None:
        """MCP HTTP 서버 URL 설정 (env 우선, 기본값 localhost)"""
        default_urls: Dict[str, str] = {
            "classroom":  "http://localhost:8101/mcp",
            "notice":     "http://localhost:8102/mcp",
            "meal":       "http://localhost:8103/mcp",
            "library":    "http://localhost:8104/mcp",
            "course":     "http://localhost:8105/mcp",
            "curriculum": "http://localhost:8106/mcp",
            "shuttle":    "http://localhost:8107/mcp",
        }
        for name, default_url in default_urls.items():
            url = os.getenv(f"MCP_{name.upper()}_URL", default_url)
            self._sessions[name] = MCPHTTPSession(name, url)
            self.server_params[name] = {"url": url}
            log.debug("MCP HTTP 등록: %s → %s", name, url)

    # ── 라이프사이클 ──────────────────────────────────────────────────────────

    async def start_all(self) -> None:
        """앱 startup 시 모든 HTTP 서버 가용성 확인"""
        results = await asyncio.gather(
            *[s.check_health() for s in self._sessions.values()],
            return_exceptions=True,
        )
        ok = sum(1 for r in results if r is True)
        log.info("MCP HTTP 서버 가용성 확인: %d/%d 정상", ok, len(self._sessions))

    async def stop_all(self) -> None:
        """HTTP 서버는 독립 프로세스 — 클라이언트 측 종료 처리 없음"""
        log.info("MCP HTTP Client 종료 (서버 프로세스는 독립 실행)")

    # ── Tool 실행 ─────────────────────────────────────────────────────────────

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        *,
        timeout: float = 10.0,
        retries: int = 1,  # API 호환성 유지
    ) -> Any:
        session = self._sessions.get(server_name)
        if not session:
            raise ValueError(f"등록되지 않은 MCP 서버: {server_name}")

        try:
            result = await session.call_tool(tool_name, arguments, timeout)
            return self._parse_result(result)
        except Exception:
            if retries > 0:
                log.warning("MCP 재시도 (%s.%s)", server_name, tool_name)
                result = await session.call_tool(tool_name, arguments, timeout)
                return self._parse_result(result)
            raise

    def _parse_result(self, result: Any) -> Any:
        """FastMCP CallToolResult → Python 객체 변환"""
        if hasattr(result, "content") and result.content:
            if isinstance(result.content, list):
                texts = [
                    item.text
                    for item in result.content
                    if hasattr(item, "text")
                ]
                if texts:
                    combined = "\n".join(texts)
                    try:
                        return json.loads(combined)
                    except json.JSONDecodeError:
                        return combined
            if hasattr(result.content, "text"):
                try:
                    return json.loads(result.content.text)
                except json.JSONDecodeError:
                    return result.content.text
        return result

    # ── Tool Discovery ────────────────────────────────────────────────────────

    async def discover_tools(self) -> list[dict]:
        """모든 HTTP MCP 서버에서 tool 목록 동적 수집 후 캐시

        Phase 2 변경: list_tools()가 HTTP 요청으로 처리 (subprocess 없음)
        inputSchema(camelCase) → input_schema(snake_case) 변환은 Claude API 요구사항
        """
        discovered: dict[str, dict] = {}

        for name, session in self._sessions.items():
            try:
                tools = await session.list_tools()
                for tool in tools:
                    if tool.name not in discovered:
                        discovered[tool.name] = {
                            "name": tool.name,
                            "description": tool.description or "",
                            "input_schema": tool.inputSchema or {"type": "object", "properties": {}},
                        }
                log.debug("Tool discovery: %s → %d tools", name, len(tools))
            except Exception as e:
                log.warning("Tool discovery 실패 (%s): %s", name, e)

        self._discovered_tools = list(discovered.values())
        log.info(
            "Tool discovery 완료: 총 %d tools (%d 서버)",
            len(self._discovered_tools),
            len(self._sessions),
        )
        return self._discovered_tools

    def get_tools(self) -> list[dict]:
        """캐시된 tool 목록 반환. discover_tools() 호출 전이면 빈 리스트."""
        return self._discovered_tools

    # ── Convenience wrappers (기존 호환) ─────────────────────────────────────

    async def meal_get_today(self, meal_type: str = "lunch") -> Any:
        return await self.call_tool("meal", "get_today_meal_tool", {"meal_type": meal_type})

    async def meal_scrape_weekly(self) -> Any:
        return await self.call_tool("meal", "scrape_weekly_meal", {})

    async def library_info(self, campus: str = "seoul") -> Any:
        return await self.call_tool("library", "get_library_info", {"campus": campus})

    async def library_seats(self, username: str, password: str, campus: str = "seoul") -> Any:
        return await self.call_tool("library", "get_seat_availability", {
            "username": username, "password": password, "campus": campus,
        })

    async def library_reserve(self, username: str, password: str, room: str, seat_number: str | None = None) -> Any:
        payload: dict = {"username": username, "password": password, "room": room}
        if seat_number:
            payload["seat_number"] = seat_number
        return await self.call_tool("library", "reserve_seat", payload)

    async def course_search(self, department: str = "소프트웨어융합학과", keyword: str | None = None) -> Any:
        payload: dict = {"department": department}
        if keyword:
            payload["keyword"] = keyword
        return await self.call_tool("course", "search_courses", payload)

    async def course_professor(self, professor: str) -> Any:
        return await self.call_tool("course", "get_professor_courses", {"professor": professor})

    async def course_by_code(self, code: str) -> Any:
        return await self.call_tool("course", "get_course_by_code", {"code": code})


# 전역 인스턴스
mcp_client = MCPClient()
