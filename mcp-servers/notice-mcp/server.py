"""
Notice MCP Server - JSON-RPC stdio 방식
"""
import asyncio
import json
import sys
import os
from pathlib import Path
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
async def tool_get_latest_notices(args: Dict) -> Dict:
    """최신 공지사항 조회"""
    db = SessionLocal()
    try:
        source = args.get("source", "swedu")
        limit = args.get("limit", 5)
        
        notices = crud.get_latest_notices(db, source, limit)
        
        results = {
            "notices": [
                {
                    "title": n.title,
                    "url": n.url,
                    "date": n.date,
                    "author": n.author,
                    "source": n.source,
                    "views": n.views if hasattr(n, 'views') else 0
                }
                for n in notices
            ]
        }
        
        return results
    finally:
        db.close()


async def tool_search_notices(args: Dict) -> Dict:
    """공지사항 검색"""
    db = SessionLocal()
    try:
        query = args.get("query", "")
        limit = args.get("limit", 5)
        
        notices = crud.search_notices(db, query, limit)
        
        results = {
            "notices": [
                {
                    "title": n.title,
                    "url": n.url,
                    "date": n.date,
                    "author": n.author,
                    "source": n.source,
                    "views": n.views if hasattr(n, 'views') else 0
                }
                for n in notices
            ]
        }
        
        return results
    finally:
        db.close()


async def tool_crawl_fresh_notices(args: Dict) -> Dict:
    """실시간 크롤링"""
    # TODO: Playwright 크롤러 실행
    return {
        "message": "크롤링 기능은 개발 중입니다",
        "notices": []
    }


# MCP 메인 루프
async def main():
    tools = {
        "get_latest_notices": tool_get_latest_notices,
        "search_notices": tool_search_notices,
        "crawl_fresh_notices": tool_crawl_fresh_notices,
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
                            "name": "get_latest_notices",
                            "description": "최신 공지사항 조회",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "source": {
                                        "type": "string",
                                        "enum": ["swedu", "department"],
                                        "description": "공지 출처"
                                    },
                                    "limit": {
                                        "type": "integer",
                                        "default": 5
                                    }
                                },
                                "required": ["source"]
                            }
                        },
                        {
                            "name": "search_notices",
                            "description": "공지사항 키워드 검색",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "검색 키워드"},
                                    "limit": {"type": "integer", "default": 5}
                                },
                                "required": ["query"]
                            }
                        },
                        {
                            "name": "crawl_fresh_notices",
                            "description": "실시간 크롤링",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "source": {"type": "string", "enum": ["swedu", "department"]},
                                    "limit": {"type": "integer", "default": 20}
                                }
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