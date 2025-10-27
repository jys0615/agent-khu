"""
Meal MCP Server
학식 메뉴 제공
"""
import sys
import json
import os
from datetime import datetime
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

sys.path.append(os.path.expanduser("~/Desktop/agent-khu/backend"))
from app.database import SessionLocal
from app import crud

server = Server("meal-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """사용 가능한 도구 목록"""
    return [
        Tool(
            name="get_today_meals",
            description="오늘의 학식 메뉴 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "cafeteria": {
                        "type": "string",
                        "enum": ["student", "faculty", "dormitory"],
                        "description": "식당 (학생, 교직원, 기숙사)",
                        "default": "student"
                    }
                }
            }
        ),
        Tool(
            name="search_menu",
            description="메뉴 검색 (예: 김치찌개)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "메뉴 이름"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="crawl_fresh_meals",
            description="실시간 학식 메뉴 크롤링",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "날짜 (YYYY-MM-DD)",
                        "default": datetime.now().strftime("%Y-%m-%d")
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
        if name == "get_today_meals":
            cafeteria = arguments.get("cafeteria", "student")
            today = datetime.now().strftime("%Y-%m-%d")
            
            # DB 조회
            meals = crud.get_meals_by_date(db, today, cafeteria)
            
            results = [
                {
                    "cafeteria": m.cafeteria,
                    "meal_type": m.meal_type,  # breakfast, lunch, dinner
                    "menu": m.menu,
                    "price": m.price,
                    "date": m.date
                }
                for m in meals
            ]
            
            return [TextContent(
                type="text",
                text=json.dumps(results, ensure_ascii=False)
            )]
        
        elif name == "search_menu":
            query = arguments.get("query", "")
            
            meals = crud.search_meals(db, query)
            
            results = [
                {
                    "cafeteria": m.cafeteria,
                    "menu": m.menu,
                    "price": m.price,
                    "date": m.date
                }
                for m in meals
            ]
            
            return [TextContent(
                type="text",
                text=json.dumps(results, ensure_ascii=False)
            )]
        
        elif name == "crawl_fresh_meals":
            # TODO: 학식 크롤러 구현
            return [TextContent(
                type="text",
                text="학식 크롤러 구현 필요"
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "Unknown tool"}, ensure_ascii=False)
            )]
    
    finally:
        db.close()


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())