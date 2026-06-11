"""
Classroom MCP Server — FastMCP + Streamable HTTP (Phase 2)
강의실 위치, 건물 정보 제공
"""
import os
import re
import sys

from fastmcp import FastMCP

backend_path = os.getenv("BACKEND_PATH", "/app")
sys.path.insert(0, backend_path)

from app.database import SessionLocal
from app import crud

PORT = int(os.getenv("PORT", "8101"))
mcp = FastMCP("classroom-mcp")


@mcp.tool()
async def search_classroom(query: str) -> dict:
    """경희대 강의실/건물 검색 (건물명, 강의실 번호로 검색)

    Args:
        query: 검색어 (예: '전101', '정보관', '201호')
    """
    db = SessionLocal()
    try:
        classrooms = crud.search_classrooms(db, query, 5)
        if not classrooms and query:
            tokens = [t.strip() for t in re.split(r"[\s호실]", query) if len(t.strip()) > 1]
            for token in tokens:
                classrooms = crud.search_classrooms(db, token, 5)
                if classrooms:
                    break

        if not classrooms:
            return {"found": False, "classrooms": [], "message": f"'{query}'에 대한 검색 결과가 없습니다."}

        return {
            "found": True,
            "count": len(classrooms),
            "classrooms": [
                {
                    "building_name": c.building_name,
                    "room_name": c.room_name,
                    "room_number": c.room_number,
                    "floor": c.floor,
                    "professor_name": c.professor_name,
                    "latitude": float(c.latitude) if c.latitude else None,
                    "longitude": float(c.longitude) if c.longitude else None,
                }
                for c in classrooms
            ],
        }
    except Exception as e:
        return {"found": False, "error": str(e), "classrooms": []}
    finally:
        db.close()


@mcp.tool()
async def get_classroom_stats() -> str:
    """강의실 통계 및 건물 목록 조회"""
    db = SessionLocal()
    try:
        stats = crud.get_classroom_stats(db)
        return f"강의실 통계:\n{stats}"
    except Exception as e:
        return f"오류: {str(e)}"
    finally:
        db.close()


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=PORT, stateless_http=True)
