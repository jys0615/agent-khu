"""
Shuttle MCP Server — 경희대 셔틀버스 다음 출발 시간 조회

노선 정보 (정적 데이터 기반):
  to_station : 국제캠퍼스 → 기흥역 / 강남역
  to_campus  : 기흥역 / 강남역 → 국제캠퍼스

※ 실제 운행 시간표는 학교 공식 홈페이지(https://www.khu.ac.kr)에서 확인하세요.
"""
import json
import sys
from datetime import datetime, time

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("shuttle-mcp")

# ── 정적 시간표 (HH:MM 문자열 리스트) ─────────────────────────────────────
# 출처: 경희대 국제캠퍼스 공식 셔틀 시간표 (2025년 기준 근사치)
SCHEDULES: dict[str, list[str]] = {
    # 국제캠퍼스 → 기흥역 방향
    "to_station": [
        "08:00", "08:30", "09:00", "09:30", "10:00",
        "11:00", "12:00", "13:00", "14:00", "15:00",
        "16:00", "17:00", "17:30", "18:00", "18:30",
        "19:00", "20:00", "21:00", "22:00",
    ],
    # 기흥역 → 국제캠퍼스 방향
    "to_campus": [
        "08:10", "08:40", "09:10", "09:40", "10:10",
        "11:10", "12:10", "13:10", "14:10", "15:10",
        "16:10", "17:10", "17:40", "18:10", "18:40",
        "19:10", "20:10", "21:10", "22:10",
    ],
}

ROUTE_LABELS = {
    "to_station": "국제캠퍼스 → 기흥역",
    "to_campus": "기흥역 → 국제캠퍼스",
}


def _get_next_shuttle(route: str) -> dict:
    """현재 시각 기준 다음 셔틀 정보 반환."""
    schedule = SCHEDULES.get(route)
    if not schedule:
        return {
            "found": False,
            "error": f"알 수 없는 노선: {route}. 사용 가능한 노선: to_station, to_campus",
        }

    now = datetime.now()
    current_minutes = now.hour * 60 + now.minute

    for slot in schedule:
        h, m = map(int, slot.split(":"))
        slot_minutes = h * 60 + m
        if slot_minutes > current_minutes:
            wait = slot_minutes - current_minutes
            return {
                "found": True,
                "route": route,
                "route_label": ROUTE_LABELS[route],
                "next_departure": slot,
                "wait_minutes": wait,
                "message": (
                    f"{ROUTE_LABELS[route]} 다음 셔틀은 "
                    f"**{slot}** 출발입니다. (약 {wait}분 후)"
                ),
                "note": "운행 시간표는 학기 중 기준이며 방학/공휴일에는 변동될 수 있습니다.",
                "official_url": "https://www.khu.ac.kr/kor/bbs/list.do?bbsId=BBSMSTR_000000001905",
            }

    return {
        "found": False,
        "route": route,
        "route_label": ROUTE_LABELS[route],
        "message": f"오늘 {ROUTE_LABELS[route]} 방향 셔틀 운행이 종료되었습니다.",
        "official_url": "https://www.khu.ac.kr/kor/bbs/list.do?bbsId=BBSMSTR_000000001905",
    }


# ── MCP 핸들러 ──────────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_next_shuttle",
            description="경희대 셔틀버스 다음 출발 시간 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "route": {
                        "type": "string",
                        "enum": ["to_station", "to_campus"],
                        "description": (
                            "to_station: 캠퍼스→기흥역, "
                            "to_campus: 기흥역→캠퍼스"
                        ),
                    }
                },
                "required": ["route"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_next_shuttle":
        route = arguments.get("route", "to_station")
        result = _get_next_shuttle(route)
        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False),
        )]
    return [TextContent(
        type="text",
        text=json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False),
    )]


if __name__ == "__main__":
    import asyncio
    asyncio.run(stdio_server(server))
