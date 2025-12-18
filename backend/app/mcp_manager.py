from .mcp_client import mcp_client
"""
MCP 서버 관리자
"""
import json
from typing import Dict, Any


class MCPServerManager:
    """MCP 서버 관리"""
    
    def __init__(self):
        self.mcp_client = mcp_client

    async def call_curriculum(self, tool: str, **kwargs):
        """Python curriculum-mcp 서버 호출"""
        result = await mcp_client.call_tool("curriculum", tool, kwargs)
        try:
            return json.loads(result)
        except Exception:
            return result


# 전역 인스턴스
mcp_manager = MCPServerManager()