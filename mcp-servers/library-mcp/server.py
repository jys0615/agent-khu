"""
Library MCP Server
도서관 좌석 정보 제공
"""
import sys
import json
import os
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

sys.path.append(os.path.expanduser("~/Desktop/agent-khu/backend"))
from app.database import SessionLocal
from app import crud

server = Server("library-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_seat_status",
            description="도서관 좌석 현황 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "열람실 위치",
                        "enum": ["central", "law", "medical"]
                    }
                }
            }
        ),
        Tool(
            name="crawl_fresh_seats",
            description="실시간 좌석 정보 크롤링",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    db = SessionLocal()
    
    try:
        if name == "get_seat_status":
            location = arguments.get("location", "central")
            
            seats = crud.get_library_seats(db, location)
            
            results = [
                {
                    "location": s.location,
                    "room_name": s.room_name,
                    "available_seats": s.available_seats,
                    "total_seats": s.total_seats,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None
                }
                for s in seats
            ]
            
            return [TextContent(
                type="text",
                text=json.dumps(results, ensure_ascii=False)
            )]
        
        elif name == "crawl_fresh_seats":
            # TODO: 도서관 좌석 크롤러
            return [TextContent(
                type="text",
                text="도서관 크롤러 구현 필요"
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