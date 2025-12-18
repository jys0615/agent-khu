"""
Classroom MCP Server - MCP SDK 호환
강의실 위치, 건물 정보 제공
"""
import asyncio
import sys
import os
from typing import Any

# MCP SDK
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Database
backend_path = os.getenv("BACKEND_PATH", "/app")
sys.path.insert(0, backend_path)

from app.database import SessionLocal
from app import crud

# Server initialization
server = Server("classroom-mcp")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="search_classroom",
            description="경희대 강의실/건물 검색 (건물명, 강의실 번호로 검색)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색어 (예: '전101', '정보관', '201호')"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_classroom_stats",
            description="강의실 통계 및 건물 목록 조회",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    
    if name == "search_classroom":
        db = SessionLocal()
        try:
            import json
            query = arguments.get("query", "")
            classrooms = crud.search_classrooms(db, query, 5)
            
            # 결과가 없으면 쿼리를 분해하여 재검색 시도
            if not classrooms and query:
                # 공백이나 특수문자로 분해
                import re
                tokens = re.split(r'[\s호실호]', query)
                tokens = [t.strip() for t in tokens if t.strip()]
                
                # 각 토큰으로 재검색
                for token in tokens:
                    if len(token) > 1:  # 너무 짧은 토큰 제외
                        classrooms = crud.search_classrooms(db, token, 5)
                        if classrooms:
                            break
            
            if not classrooms:
                result = json.dumps({
                    "found": False,
                    "classrooms": [],
                    "message": f"'{query}'에 대한 검색 결과가 없습니다."
                }, ensure_ascii=False)
            else:
                classrooms_data = []
                for c in classrooms:
                    classrooms_data.append({
                        "building_name": c.building_name,
                        "room_name": c.room_name,
                        "room_number": c.room_number,
                        "floor": c.floor,
                        "professor_name": c.professor_name,
                        "latitude": float(c.latitude) if c.latitude else None,
                        "longitude": float(c.longitude) if c.longitude else None
                    })
                result = json.dumps({
                    "found": True,
                    "classrooms": classrooms_data,
                    "count": len(classrooms_data)
                }, ensure_ascii=False)
        except Exception as e:
            import json
            result = json.dumps({
                "found": False,
                "error": str(e),
                "classrooms": []
            }, ensure_ascii=False)
        finally:
            db.close()
        
        return [TextContent(type="text", text=result)]
    
    elif name == "get_classroom_stats":
        db = SessionLocal()
        try:
            stats = crud.get_classroom_stats(db)
            result = f"강의실 통계:\n{stats}"
        except Exception as e:
            result = f"오류: {str(e)}"
        finally:
            db.close()
        
        return [TextContent(type="text", text=result)]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Main entry point"""
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
