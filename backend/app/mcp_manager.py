"""
MCP 서버 관리자 - sitemcp 통합
"""
import asyncio
import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path


class MCPServerManager:
    """MCP 서버 관리"""
    
    def __init__(self):
        self.processes = {}
        self.sitemcp_path = Path.home() / "Desktop/agent-khu/mcp-servers/sitemcp/dist/cli.mjs"
        
    async def start_sitemcp(self, site_url: str, site_name: str):
        """sitemcp 서버 시작"""
        
        # sitemcp를 MCP 서버 모드로 실행
        process = await asyncio.create_subprocess_exec(
            "node",
            str(self.sitemcp_path),
            site_url,
            "--concurrency", "5",
            "--max-length", "3000",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        self.processes[site_name] = process
        print(f"✅ sitemcp [{site_name}] 시작: {site_url}")
        
        return process
    
    async def start_all_sites(self):
        """모든 경희대 사이트 MCP 서버 시작"""
        sites = {
            "khu-swedu": "https://swedu.khu.ac.kr/bbs/board.php?bo_table=07_01",
            "khu-cs": "https://ce.khu.ac.kr/ce/notice/notice.do"
        }
        
        for name, url in sites.items():
            await self.start_sitemcp(url, name)
        
        print("🚀 모든 sitemcp 서버 시작 완료")
    
    async def call_sitemcp(
        self,
        site_name: str,
        action: str,
        params: Dict[str, Any]
    ) -> Any:
        """sitemcp에 요청 전송"""
        
        process = self.processes.get(site_name)
        
        if not process:
            raise ValueError(f"sitemcp server '{site_name}' not running")
        
        # MCP JSON-RPC 요청
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": f"tools/call",
            "params": {
                "name": action,
                "arguments": params
            }
        }
        
        # 요청 전송
        request_json = json.dumps(request) + "\n"
        process.stdin.write(request_json.encode())
        await process.stdin.drain()
        
        # 응답 읽기
        response_line = await process.stdout.readline()
        
        if not response_line:
            return None
        
        response = json.loads(response_line.decode())
        
        if "error" in response:
            raise Exception(f"MCP error: {response['error']}")
        
        return response.get("result", {}).get("content", [])
    
    async def stop_all(self):
        """모든 MCP 서버 종료"""
        for name, process in self.processes.items():
            process.terminate()
            await process.wait()
            print(f"🛑 {name} 서버 종료")


# 전역 인스턴스
mcp_manager = MCPServerManager()