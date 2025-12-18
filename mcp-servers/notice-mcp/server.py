"""Notice MCP Server - official MCP server SDK version."""
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import service


server = Server("notice-mcp")


def json_content(payload) -> list:
    """Return MCP TextContent with JSON mime type."""
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False), mimeType="application/json")]


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_latest_notices",
            description="학과별 최신 공지 (학과명 또는 코드)",
            inputSchema={
                "type": "object",
                "properties": {
                    "department": {"type": "string"},
                    "limit": {"type": "integer"},
                },
            },
        ),
        Tool(
            name="search_notices",
            description="공지사항 키워드 검색",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                    "department": {"type": "string"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="crawl_fresh_notices",
            description="학과 공지 크롤링 (키워드 필터 지원)",
            inputSchema={
                "type": "object",
                "properties": {
                    "department": {"type": "string"},
                    "limit": {"type": "integer"},
                    "keyword": {"type": "string"},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "get_latest_notices":
            department = arguments.get("department", "소프트웨어융합학과")
            limit = arguments.get("limit", 5)
            _, result = service.list_latest_notices(department, limit)
            return json_content(result)

        if name == "search_notices":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 5)
            department = arguments.get("department")
            result = service.search_notices(query, limit, department)
            return json_content(result)

        if name == "crawl_fresh_notices":
            department = arguments.get("department", "소프트웨어융합학과")
            limit = arguments.get("limit", 20)
            keyword = arguments.get("keyword")
            result = service.crawl_and_persist(department, limit, keyword)
            return json_content(result)

        return json_content({"error": {"type": "UnknownTool", "message": f"Unknown tool: {name}"}})

    except Exception as e:
        return json_content({"error": {"type": "ServerError", "message": str(e)}})


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
