"""
Notice MCP Server
공지사항 크롤링 및 제공
"""
import sys
import json
import subprocess
import os
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# DB 연결
sys.path.append(os.path.expanduser("~/Desktop/agent-khu/backend"))
from app.database import SessionLocal
from app import crud

server = Server("notice-mcp")

SCRAPER_PATH = os.path.expanduser(
    "~/Desktop/agent-khu/mcp-servers/notice-mcp/scrapers/khu_scraper.py"
)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """사용 가능한 도구 목록"""
    return [
        Tool(
            name="get_latest_notices",
            description="최신 공지사항 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "enum": ["swedu", "department"],
                        "description": "공지 출처"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 5,
                        "description": "결과 개수"
                    }
                },
                "required": ["source"]
            }
        ),
        Tool(
            name="search_notices",
            description="공지사항 키워드 검색",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색 키워드"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="crawl_fresh_notices",
            description="실시간 공지사항 크롤링 (Playwright)",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "enum": ["swedu", "department"],
                        "default": "swedu"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20
                    }
                }
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """도구 실행"""
    db = SessionLocal()
    
    try:
        if name == "get_latest_notices":
            source = arguments.get("source", "swedu")
            limit = arguments.get("limit", 5)
            
            notices = crud.get_latest_notices(db, source, limit)
            
            results = [
                {
                    "title": n.title,
                    "url": n.url,
                    "date": n.date,
                    "author": n.author,
                    "source": n.source,
                    "views": n.views if hasattr(n, 'views') else 0  # 추가!
                }
                for n in notices
            ]
            
            return [TextContent(
                type="text",
                text=json.dumps(results, ensure_ascii=False)
            )]
        
        elif name == "search_notices":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 5)
            
            notices = crud.search_notices(db, query, limit)
            
            results = [
                {
                    "title": n.title,
                    "url": n.url,
                    "date": n.date,
                    "author": n.author,
                    "source": n.source,
                    "views": n.views if hasattr(n, 'views') else 0  # 추가!
                }
                for n in notices
            ]
            
            return [TextContent(
                type="text",
                text=json.dumps(results, ensure_ascii=False)
            )]
        
        elif name == "crawl_fresh_notices":
            # ... (동일)
            source = arguments.get("source", "swedu")
            limit = arguments.get("limit", 20)
            
            # Playwright 크롤러 실행
            if os.path.exists(SCRAPER_PATH):
                result = subprocess.run(
                    ["python3", SCRAPER_PATH, source, str(limit)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    posts = json.loads(result.stdout)
                    
                    # DB 저장
                    new_count = 0
                    for post in posts:
                        if crud.create_notice_from_mcp(db, post):
                            new_count += 1
                    
                    return [TextContent(
                        type="text",
                        text=f"크롤링 완료: {new_count}개 신규 공지 저장"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"크롤링 실패: {result.stderr}"
                    )]
            else:
                return [TextContent(
                    type="text",
                    text=f"크롤러 파일 없음: {SCRAPER_PATH}"
                )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "Unknown tool"}, ensure_ascii=False)
            )]
    
    finally:
        db.close()


async def main():
    """MCP Server 시작"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())