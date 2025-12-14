"""
Classroom MCP Server - MCP SDK 호환
"""
import asyncio
import json
import sys
import os
from typing import Any, Dict

backend_path = os.getenv("BACKEND_PATH", "/app")
sys.path.insert(0, backend_path)

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


async def tool_search_room(args: Dict) -> Dict:
    db = SessionLocal()
    try:
        query = args.get("query", "")
        classrooms = crud.search_classrooms(db, query, 5)
        
        if not classrooms:
            return {"found": False, "message": f"'{query}'에 대한 검색 결과가 없습니다."}
        
        return {
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
                    "is_accessible": c.is_accessible,
                    "latitude": c.latitude,
                    "longitude": c.longitude
                }
                for c in classrooms
            ]
        }
    except Exception as e:
        return {"found": False, "error": str(e)}
    finally:
        db.close()


async def tool_get_classroom_stats(args: Dict) -> Dict:
    db = SessionLocal()
    try:
        return crud.get_classroom_stats(db)
    finally:
        db.close()


async def main():
    tools = {
        "search_classroom": tool_search_room,
        "get_classroom_stats": tool_get_classroom_stats,
    }
    
    while True:
        msg = _readline()
        if msg is None:
            break
        
        if msg.get("method") == "initialize":
            _send({
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "classroom-mcp",
                        "version": "1.0.0"
                    }
                }
            })
            continue
        
        if msg.get("method") == "notifications/initialized":
            continue
        
        if msg.get("method") == "tools/list":
            _send({
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "search_classroom",
                            "description": "경희대 전자정보대학관 공간 검색",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string"}
                                },
                                "required": ["query"]
                            }
                        },
                        {
                            "name": "get_classroom_stats",
                            "description": "강의실 통계",
                            "inputSchema": {"type": "object", "properties": {}}
                        }
                    ]
                }
            })
            continue
        
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
        
        if "id" in msg:
            _result(msg["id"], {"status": "noop"})


if __name__ == "__main__":
    asyncio.run(main())
