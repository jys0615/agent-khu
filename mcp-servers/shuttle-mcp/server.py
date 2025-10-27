"""
Shuttle MCP Server
셔틀버스 정보 제공
"""
import sys
import json
import os
from datetime import datetime, timedelta
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

sys.path.append(os.path.expanduser("~/Desktop/agent-khu/backend"))
from app.database import SessionLocal
from app import crud

server = Server("shuttle-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_next_bus",
            description="다음 셔틀버스 시간 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "route": {
                        "type": "string",
                        "enum": ["seoul", "suwon", "shuttle"],
                        "description": "노선 (서울, 수원, 셔틀)"
                    },
                    "station": {
                        "type": "string",
                        "description": "정류장"
                    }
                },
                "required": ["route"]
            }
        ),
        Tool(
            name="get_shuttle_schedule",
            description="셔틀버스 전체 시간표",
            inputSchema={
                "type": "object",
                "properties": {
                    "route": {
                        "type": "string",
                        "enum": ["seoul", "suwon", "shuttle"]
                    }
                },
                "required": ["route"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    db = SessionLocal()
    
    try:
        if name == "get_next_bus":
            route = arguments.get("route", "shuttle")
            station = arguments.get("station", "본관")
            
            # 현재 시간 이후 버스 찾기
            now = datetime.now().time()
            
            buses = crud.get_next_shuttle(db, route, station, now)
            
            if buses:
                next_bus = buses[0]
                result = {
                    "route": next_bus.route,
                    "station": next_bus.station,
                    "departure_time": next_bus.departure_time.isoformat(),
                    "destination": next_bus.destination,
                    "minutes_until": int((datetime.combine(datetime.today(), next_bus.departure_time) - 
                                         datetime.combine(datetime.today(), now)).total_seconds() / 60)
                }
            else:
                result = {"message": "운행 종료"}
            
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False)
            )]
        
        elif name == "get_shuttle_schedule":
            route = arguments.get("route", "shuttle")
            
            schedules = crud.get_shuttle_schedule(db, route)
            
            results = [
                {
                    "route": s.route,
                    "station": s.station,
                    "departure_time": s.departure_time.isoformat(),
                    "destination": s.destination
                }
                for s in schedules
            ]
            
            return [TextContent(
                type="text",
                text=json.dumps(results, ensure_ascii=False)
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