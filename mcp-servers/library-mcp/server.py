"""
Library MCP Server - 경희대 도서관 좌석 조회
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict

from scraper import get_seat_availability, reserve_seat

# 데이터 경로
DATA_PATH = Path(__file__).parent / "data" / "library_info.json"


def load_library_info() -> Dict:
    """도서관 정보 로드"""
    if not DATA_PATH.exists():
        return {}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# MCP 표준 IO 함수
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
async def tool_get_library_info(args: Dict) -> Dict:
    """도서관 기본 정보 조회 (로그인 불필요)"""
    data = load_library_info()
    campus = args.get("campus", "seoul")
    
    if campus not in data.get("libraries", {}):
        return {"error": f"Unknown campus: {campus}", "available": list(data.get("libraries", {}).keys())}
    
    return data["libraries"][campus]


async def tool_get_seat_availability(args: Dict) -> Dict:
    """좌석 현황 조회 (로그인 필요)"""
    username = args.get("username")
    password = args.get("password")
    campus = args.get("campus", "seoul")
    
    if not username or not password:
        return {
            "error": "로그인이 필요합니다",
            "required": ["username", "password"],
            "message": "학번과 비밀번호를 입력해주세요"
        }
    
    try:
        result = await get_seat_availability(username, password, campus)
        return result
    except Exception as e:
        return {
            "error": str(e),
            "message": "좌석 현황 조회 실패. 로그인 정보를 확인하세요."
        }


async def tool_reserve_seat(args: Dict) -> Dict:
    """좌석 예약 (로그인 필요)"""
    username = args.get("username")
    password = args.get("password")
    room = args.get("room")
    seat_number = args.get("seat_number")
    
    if not username or not password:
        return {"error": "로그인이 필요합니다"}
    
    if not room:
        return {"error": "예약할 열람실을 지정해주세요"}
    
    try:
        result = await reserve_seat(username, password, room, seat_number)
        return result
    except Exception as e:
        return {"error": str(e)}


# MCP 메인 루프
async def main():
    tools = {
        "get_library_info": tool_get_library_info,
        "get_seat_availability": tool_get_seat_availability,
        "reserve_seat": tool_reserve_seat,
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
                    "capabilities": {"tools": {}}, "serverInfo": {"name": "library-mcp", "version": "1.0.0"}
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
                            "name": "get_library_info",
                            "description": "도서관 기본 정보 조회 (로그인 불필요)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "campus": {
                                        "type": "string",
                                        "enum": ["seoul", "global"],
                                        "description": "캠퍼스 (seoul: 서울, global: 국제)"
                                    }
                                }
                            }
                        },
                        {
                            "name": "get_seat_availability",
                            "description": "도서관 좌석 현황 실시간 조회 (로그인 필요)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "username": {"type": "string", "description": "학번"},
                                    "password": {"type": "string", "description": "비밀번호"},
                                    "campus": {"type": "string", "description": "캠퍼스"}
                                },
                                "required": ["username", "password"]
                            }
                        },
                        {
                            "name": "reserve_seat",
                            "description": "도서관 좌석 예약 (로그인 필요)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "username": {"type": "string", "description": "학번"},
                                    "password": {"type": "string", "description": "비밀번호"},
                                    "room": {"type": "string", "description": "열람실 이름"},
                                    "seat_number": {"type": "string", "description": "좌석 번호 (선택)"}
                                },
                                "required": ["username", "password", "room"]
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
