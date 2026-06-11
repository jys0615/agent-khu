"""
Library MCP Server — FastMCP + Streamable HTTP (Phase 2)
도서관 정보, 좌석 현황, 예약
"""
import os
import sys
from pathlib import Path

from fastmcp import FastMCP

CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))
sys.path.insert(0, str(CURRENT_DIR.parent))

try:
    from .service import load_library_info, get_seat_availability_service, reserve_seat_service
except Exception:
    from service import load_library_info, get_seat_availability_service, reserve_seat_service

PORT = int(os.getenv("PORT", "8104"))
mcp = FastMCP("library-mcp")


@mcp.tool()
async def get_library_info(campus: str = "seoul") -> dict:
    """도서관 기본 정보 조회 (로그인 불필요)

    Args:
        campus: 캠퍼스 — seoul(서울) 또는 global(국제)
    """
    data = load_library_info()
    libraries = data.get("libraries", {})
    if campus not in libraries:
        return {"error": f"Unknown campus: {campus}", "available": list(libraries.keys())}
    return libraries[campus]


@mcp.tool()
async def get_seat_availability(username: str, password: str, campus: str = "seoul") -> dict:
    """도서관 좌석 현황 실시간 조회 (로그인 필요)

    Args:
        username: 학생 ID
        password: 비밀번호
        campus: 캠퍼스 (기본값: seoul)
    """
    return await get_seat_availability_service({"username": username, "password": password, "campus": campus})


@mcp.tool()
async def reserve_seat(username: str, password: str, room: str, seat_number: str = "") -> dict:
    """도서관 좌석 예약 (로그인 필요)

    Args:
        username: 학생 ID
        password: 비밀번호
        room: 열람실 이름
        seat_number: 좌석 번호 (비워두면 자동 배정)
    """
    payload = {"username": username, "password": password, "room": room}
    if seat_number:
        payload["seat_number"] = seat_number
    return await reserve_seat_service(payload)


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=PORT, stateless_http=True)
