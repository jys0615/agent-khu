"""
Meal MCP Server — FastMCP + Streamable HTTP (Phase 2)
오늘의 학식 메뉴 조회, 식당 정보, 주간 식단 스크래핑
"""
import os
import sys
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))
sys.path.insert(0, str(CURRENT_DIR.parent))

try:
    from .service import get_today_meal, get_cafeteria_info_service, scrape_weekly_meal_service
except Exception:
    from service import get_today_meal, get_cafeteria_info_service, scrape_weekly_meal_service

PORT = int(os.getenv("PORT", "8103"))
mcp = FastMCP("meal-mcp")


@mcp.tool()
async def get_today_meal_tool(meal_type: str = "lunch") -> dict:
    """오늘의 학식 메뉴 조회 (Vision API로 식단표 이미지 분석, 캐시 우선 사용)

    Args:
        meal_type: 식사 시간 — lunch(점심) 또는 dinner(저녁)
    """
    return await get_today_meal({"meal_type": meal_type})


@mcp.tool()
async def get_cafeteria_info() -> dict:
    """식당 기본 정보 조회 (위치, 운영시간, 가격)"""
    return get_cafeteria_info_service()


@mcp.tool()
async def scrape_weekly_meal() -> dict:
    """주간 식단표 전체 스크래핑 (관리자용 — 캐시 갱신)"""
    return await scrape_weekly_meal_service()


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=PORT, stateless_http=True)
