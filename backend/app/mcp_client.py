"""
MCP Client for FastAPI
KHU Notice MCP Server와 통신
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class KHUNoticeMCPClient:
    """KHU Notice MCP Server 클라이언트"""
    
    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
    
    async def get_sw_notices(self, limit: int = 10, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        SW중심대학사업단 공지사항 가져오기
        """
        server_params = StdioServerParameters(
            command="node",
            args=[self.server_script_path],
            env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "get_sw_notices",
                    arguments={"limit": limit, "force_refresh": force_refresh}
                )
                
                if result.content and len(result.content) > 0:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        return json.loads(content.text)
                
                return []
    
    async def get_department_notices(self, limit: int = 10, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        소프트웨어융합대학 공지사항 가져오기
        """
        server_params = StdioServerParameters(
            command="node",
            args=[self.server_script_path],
            env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "get_department_notices",
                    arguments={"limit": limit, "force_refresh": force_refresh}
                )
                
                if result.content and len(result.content) > 0:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        return json.loads(content.text)
                
                return []
    
    async def get_academic_schedule(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        학사일정 가져오기
        """
        server_params = StdioServerParameters(
            command="node",
            args=[self.server_script_path],
            env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "get_academic_schedule",
                    arguments={"force_refresh": force_refresh}
                )
                
                if result.content and len(result.content) > 0:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        return json.loads(content.text)
                
                return []
    
    async def search_notices(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        공지사항 검색
        """
        server_params = StdioServerParameters(
            command="node",
            args=[self.server_script_path],
            env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "search_notices",
                    arguments={"query": query, "limit": limit}
                )
                
                if result.content and len(result.content) > 0:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        return json.loads(content.text)
                
                return []


# 싱글톤 인스턴스
khu_notice_mcp_client = KHUNoticeMCPClient(
    server_script_path="/Users/jung-yoonsuh/Desktop/agent-khu/mcp-servers/khu-notice-mcp/dist/index.js"
)