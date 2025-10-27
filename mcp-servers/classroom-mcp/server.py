"""
Classroom MCP Server
강의실 정보 제공
"""
import sys
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# DB 연결 (FastAPI와 동일)
import os
sys.path.append(os.path.expanduser("~/Desktop/agent-khu/backend"))
from app.database import SessionLocal
from app import crud

server = Server("classroom-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """사용 가능한 도구 목록"""
    return [
        Tool(
            name="search_classroom",
            description="경희대 전자정보대학관 공간 검색",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색어"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_classroom_stats",
            description="공간 통계 정보",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """도구 실행"""
    db = SessionLocal()
    
    try:
        if name == "search_classroom":
            query = arguments.get("query", "")
            
            # DB에서 검색
            classrooms = crud.search_classrooms(db, query, 1)
            
            # 결과를 올바른 형식으로 변환
            results = []
            for c in classrooms:
                results.append({
                    "code": c.code,
                    "building_name": c.building_name,
                    "room_number": c.room_number,
                    "floor": c.floor,
                    "room_name": c.room_name,
                    "room_type": c.room_type,
                    "professor_name": c.professor_name,
                    "is_accessible": c.is_accessible,
                    "latitude": c.latitude,
                    "longitude": c.longitude
                })
            
            # MCP TextContent 형식으로 반환
            return [TextContent(
                type="text",
                text=json.dumps(results, ensure_ascii=False)
            )]
        
        elif name == "get_classroom_stats":
            stats = crud.get_classroom_stats(db)
            return [TextContent(
                type="text",
                text=json.dumps(stats, ensure_ascii=False)
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