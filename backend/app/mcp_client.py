"""
MCP Client for FastAPI
Instagram MCP Server와 통신
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class InstagramMCPClient:
    """Instagram MCP Server 클라이언트"""
    
    def __init__(self, server_script_path: str):
        self.server_script_path = server_script_path
    
    async def get_posts(self, limit: int = 10, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Instagram 게시물 가져오기
        """
        server_params = StdioServerParameters(
            command="node",
            args=[self.server_script_path],
            env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Tool 호출
                result = await session.call_tool(
                    "get_instagram_posts",
                    arguments={"limit": limit, "force_refresh": force_refresh}
                )
                
                # 결과 파싱
                if result.content and len(result.content) > 0:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        return json.loads(content.text)
                
                return []
    
    async def search_posts(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        게시물 검색
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
                    "search_posts",
                    arguments={"query": query, "limit": limit}
                )
                
                if result.content and len(result.content) > 0:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        return json.loads(content.text)
                
                return []


# 싱글톤 인스턴스
instagram_mcp_client = InstagramMCPClient(
    server_script_path="/Users/jung-yoonsuh/Desktop/agent-khu/mcp-servers/instagram-mcp/dist/index.js"
)