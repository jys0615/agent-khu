"""
Meal MCP Server - Official MCP Server SDK migration
Provides tools to get today's meals via Vision, cafeteria info, and weekly scraping.
"""
import asyncio
import json
import os
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

# 패키지/스크립트 실행 모두 지원: /mcp-servers/meal-mcp 경로를 모듈 검색에 추가
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))
sys.path.insert(0, str(CURRENT_DIR.parent))

# Local service layer
try:
    # 패키지 형태
    from .service import get_today_meal, get_cafeteria_info_service, scrape_weekly_meal_service
except Exception:
    # 스크립트 형태
    from service import get_today_meal, get_cafeteria_info_service, scrape_weekly_meal_service


server = Server("meal-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_today_meal",
            description=(
                "오늘의 학식 메뉴 조회 (Vision API로 식단표 이미지 분석). "
                "캐시된 주간 데이터 우선 사용. 결과에 원본 사이트 링크 포함"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "meal_type": {
                        "type": "string",
                        "enum": ["lunch", "dinner"],
                        "default": "lunch",
                        "description": "식사 시간"
                    }
                },
                "required": []
            },
        ),
        Tool(
            name="get_cafeteria_info",
            description="식당 기본 정보 (위치, 운영시간, 가격)",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="scrape_weekly_meal",
            description="주간 식단표 전체 스크래핑 (관리자용)",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


def _json_content(payload: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False), mimeType="application/json")]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any] | None) -> list[TextContent]:
    args = arguments or {}
    if name == "get_today_meal":
        payload = await get_today_meal(args)
        return _json_content(payload)
    if name == "get_cafeteria_info":
        payload = get_cafeteria_info_service()
        return _json_content(payload)
    if name == "scrape_weekly_meal":
        payload = await scrape_weekly_meal_service()
        return _json_content(payload)
    return _json_content({"error": f"Unknown tool: {name}"})


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())