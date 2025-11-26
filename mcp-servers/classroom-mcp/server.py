"""
Classroom MCP Server - JSON-RPC stdio 방식
"""
import asyncio
import json
import sys
import os
from typing import Any, Dict

# DB 연결
sys.path.append(os.path.expanduser("~/Desktop/agent-khu/backend"))
from app.database import SessionLocal
from app import crud


def _readline():
    line = sys.stdin.readline()
    if not line:
        return None
    try:
        return json.loads(line.strip())
    except Exception:
        return None


def _send(obj: dict):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _result(id_: int, data: Any, is_error: bool = False):
    content = [{"type": "text", "text": json.dumps(data, ensure_ascii=False, indent=2)}]
    res = {
        "jsonrpc": "2.0",
        "id": id_,
        "result": {"content": content, "isError": is_error}
    }
    _send(res)


# Tools
async def tool_search_room(args: Dict) -> Dict:
    """강의실 검색"""
    db = SessionLocal()
    try:
        query = args.get("query", "")
        
        # DB에서 검색
        classrooms = crud.search_classrooms(db, query, 5)
        
        if not classrooms:
            return {
                "found": False,
                "message": f"'{query}'에 대한 검색 결과가 없습니다."
            }
        
        # 결과 변환
        results = {
            "found": True,
            "rooms": [
                {
                    "code": c.code,
                    "building": c.building_name,
                    "floor": c.floor,
                    "name": c.room_name,
                    "room_number": c.room_number,
                    "room_type": c.room_type,
                    "professor_name": c.professor_name,
                    "description": f"{c.room_name} ({c.room_type})",
                    "is_accessible": c.is_accessible,
                    "latitude": c.latitude,
                    "longitude": c.longitude
                }
                for c in classrooms
            ]
        }
        
        return results
    except Exception as e:
        return {
            "found": False,
            "error": str(e),
            "message": f"검색 중 오류 발생: {str(e)}"
        }
    finally:
        db.close()


async def tool_get_classroom_stats(args: Dict) -> Dict:
    """강의실 통계"""
    db = SessionLocal()
    try:
        stats = crud.get_classroom_stats(db)
        return stats
    finally:
        db.close()


# MCP 메인 루프
async def main():
    tools = {
        "search_room": tool_search_room,
        "get_classroom_stats": tool_get_classroom_stats,
    }
    
    while True:
        msg = _readline()
        if msg is None:
            break
        
        # initialize
        if msg.get("method") == "initialize":
            _send({
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}}
                }
            })
            continue
        
        # notifications/initialized
        if msg.get("method") == "notifications/initialized":
            continue
        
        # tools/list
        if msg.get("method") == "tools/list":
            _send({
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "search_room",
                            "description": "경희대 전자정보대학관 공간 검색 (강의실, 연구실, 편의시설)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "검색어 (예: 전101, 김교수, 휴게실)"
                                    }
                                },
                                "required": ["query"]
                            }
                        },
                        {
                            "name": "get_classroom_stats",
                            "description": "강의실 통계 정보",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        }
                    ]
                }
            })
            continue
        
        # tools/call
        if msg.get("method") == "tools/call":
            req_id = msg.get("id")
            params = msg.get("params", {})
            name = params.get("name")
            arguments = params.get("arguments", {})
            
            if name not in tools:
                _result(req_id, {"error": f"Unknown tool: {name}"}, is_error=True)
                continue
            
            try:
                result = await tools[name](arguments)
                _result(req_id, result)
            except Exception as e:
                _result(req_id, {"error": str(e)}, is_error=True)
            continue
        
        # 기타
        if "id" in msg:
            _result(msg["id"], {"status": "noop"})


if __name__ == "__main__":
    asyncio.run(main())