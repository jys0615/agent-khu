"""
Meal MCP Server - JSON-RPC stdio 방식
Vision API로 식단표 이미지 읽기
"""
import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Any, Dict

# Scraper import
sys.path.append(str(Path(__file__).parent))
try:
    from scraper import get_today_meal_with_vision, get_cafeteria_info
except ImportError:
    print("⚠️ scraper.py를 찾을 수 없습니다", file=sys.stderr)


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
async def tool_get_today_meal(args: Dict) -> Dict:
    """오늘의 학식 메뉴 (Vision API)"""
    try:
        # Claude API Key 가져오기
        # Backend에서 환경변수로 전달되거나, .env 파일에서 읽기
        api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            # .env 파일 읽기 시도
            env_path = Path(__file__).parents[2] / "backend" / ".env"
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("ANTHROPIC_API_KEY="):
                            api_key = line.split("=", 1)[1].strip()
                            break
        
        if not api_key:
            return {
                "error": "API Key 없음",
                "message": "ANTHROPIC_API_KEY 환경변수를 설정해주세요"
            }
        
        meal_type = args.get("meal_type", "lunch")
        
        # Vision API로 메뉴 추출
        result = await get_today_meal_with_vision(api_key, meal_type)
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "message": "식단 조회 중 오류가 발생했습니다"
        }


async def tool_get_cafeteria_info(args: Dict) -> Dict:
    """식당 기본 정보"""
    return get_cafeteria_info()


# MCP 메인 루프
async def main():
    tools = {
        "get_today_meal": tool_get_today_meal,
        "get_cafeteria_info": tool_get_cafeteria_info,
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
                            "name": "get_today_meal",
                            "description": "오늘의 학식 메뉴 조회 (Vision API로 식단표 이미지 분석)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "meal_type": {
                                        "type": "string",
                                        "enum": ["lunch", "dinner"],
                                        "default": "lunch",
                                        "description": "식사 시간"
                                    }
                                }
                            }
                        },
                        {
                            "name": "get_cafeteria_info",
                            "description": "식당 기본 정보 (위치, 운영시간, 가격)",
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
                import traceback
                traceback.print_exc()
                _result(req_id, {"error": str(e)}, is_error=True)
            continue
        
        # 기타
        if "id" in msg:
            _result(msg["id"], {"status": "noop"})


if __name__ == "__main__":
    asyncio.run(main())