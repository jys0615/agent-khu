"""
Library MCP Server - SDK-based implementation for seat availability and reservations
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

from mcp.server import Server
from mcp.server.stdio import stdio_server

# 호환성: 구버전 mcp 패키지에는 models.Tool이 없을 수 있어 types에서 가져온다
try:
    from mcp.server.models import Tool, TextContent  # type: ignore
except Exception:  # pragma: no cover - fallback for older SDK
    from mcp.types import Tool, TextContent

# 패키지/스크립트 실행 모두 지원
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))
sys.path.insert(0, str(CURRENT_DIR.parent))

try:
    from .service import (
        load_library_info,
        get_seat_availability_service,
        reserve_seat_service,
    )
except Exception:
    from service import (
        load_library_info,
        get_seat_availability_service,
        reserve_seat_service,
    )


server = Server("library-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_library_info",
            description="도서관 기본 정보 조회 (로그인 불필요)",
            inputSchema={
                "type": "object",
                "properties": {
                    "campus": {
                        "type": "string",
                        "enum": ["seoul", "global"],
                        "description": "캠퍼스"
                    }
                },
            },
        ),
        Tool(
            name="get_seat_availability",
            description="도서관 좌석 현황 실시간 조회 (로그인 필요)",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "password": {"type": "string"},
                    "campus": {"type": "string", "default": "seoul"},
                },
            },
        ),
        Tool(
            name="reserve_seat",
            description="도서관 좌석 예약 (로그인 필요)",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {"type": "string"},
                    "password": {"type": "string"},
                    "room": {"type": "string"},
                    "seat_number": {"type": "string"},
                },
                "required": ["username", "password", "room"],
            },
        ),
    ]


def _json(payload: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False), mimeType="application/json")]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any] | None) -> list[TextContent]:
    args = arguments or {}
    if name == "get_library_info":
        campus = args.get("campus", "seoul")
        data = load_library_info()
        if campus not in data.get("libraries", {}):
            return _json({"error": f"Unknown campus: {campus}", "available": list(data.get("libraries", {}).keys())})
        return _json(data["libraries"][campus])
    if name == "get_seat_availability":
        payload = await get_seat_availability_service(args)
        return _json(payload)
    if name == "reserve_seat":
        payload = await reserve_seat_service(args)
        return _json(payload)
    return _json({"error": f"Unknown tool: {name}"})


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
