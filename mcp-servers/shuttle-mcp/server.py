"""
Shuttle MCP Server — FastMCP + Streamable HTTP (Phase 2)
경희대 셔틀버스 다음 출발 시간 조회

노선 정보 (정적 데이터 기반):
  to_station : 국제캠퍼스 → 기흥역 / 강남역
  to_campus  : 기흥역 / 강남역 → 국제캠퍼스

※ 실제 운행 시간표는 학교 공식 홈페이지(https://www.khu.ac.kr)에서 확인하세요.
"""
import os
from datetime import datetime
from typing import Literal

from fastmcp import FastMCP

PORT = int(os.getenv("PORT", "8107"))
mcp = FastMCP("shuttle-mcp")

SCHEDULES: dict[str, list[str]] = {
    "to_station": [
        "08:00", "08:30", "09:00", "09:30", "10:00",
        "11:00", "12:00", "13:00", "14:00", "15:00",
        "16:00", "17:00", "17:30", "18:00", "18:30",
        "19:00", "20:00", "21:00", "22:00",
    ],
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


@mcp.tool()
async def get_next_shuttle(route: Literal["to_station", "to_campus"] = "to_station") -> dict:
    """경희대 셔틀버스 다음 출발 시간 조회

    Args:
        route: 노선 — to_station(캠퍼스→기흥역) 또는 to_campus(기흥역→캠퍼스)
    """
    schedule = SCHEDULES.get(route)
    if not schedule:
        return {"found": False, "error": f"알 수 없는 노선: {route}"}

    now = datetime.now()
    cur_min = now.hour * 60 + now.minute

    for slot in schedule:
        h, m = map(int, slot.split(":"))
        slot_min = h * 60 + m
        if slot_min > cur_min:
            wait = slot_min - cur_min
            return {
                "found": True,
                "route": route,
                "route_label": ROUTE_LABELS[route],
                "next_departure": slot,
                "wait_minutes": wait,
                "message": f"{ROUTE_LABELS[route]} 다음 셔틀은 **{slot}** 출발입니다. (약 {wait}분 후)",
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


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=PORT, stateless_http=True)
