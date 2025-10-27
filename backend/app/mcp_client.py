"""
MCP 클라이언트 - MCP Server들과 stdio 통신
"""
import asyncio
import json
from typing import Dict, Any
from pathlib import Path


class MCPClient:
    """MCP Server와 통신하는 클라이언트"""
    
    def __init__(self):
        self.servers = {}
        self.mcp_dir = Path.home() / "Desktop/agent-khu/mcp-servers"
    
    async def start_server(self, server_name: str, server_path: str):
        """MCP Server 프로세스 시작 및 초기화"""
        process = await asyncio.create_subprocess_exec(
            "python3",
            str(server_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # 1. 초기화 요청
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "agent-khu", "version": "1.0"}
            }
        }
        
        process.stdin.write((json.dumps(init_request) + "\n").encode())
        await process.stdin.drain()
        
        # 2. 초기화 응답 대기
        try:
            init_response_line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=5.0
            )
            init_response = json.loads(init_response_line.decode())
            
            if "error" in init_response:
                raise Exception(f"MCP 초기화 실패: {init_response['error']}")
            
            print(f"✅ MCP '{server_name}' 초기화 응답 수신")
            
        except asyncio.TimeoutError:
            raise Exception(f"MCP '{server_name}' 초기화 타임아웃")
        
        # 3. initialized notification 전송 (핵심!)
        initialized_notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        process.stdin.write((json.dumps(initialized_notif) + "\n").encode())
        await process.stdin.drain()
        
        await asyncio.sleep(0.1)
        
        print(f"✅ MCP '{server_name}' 초기화 완료")
        
        # 4. 저장
        self.servers[server_name] = {
            "process": process,
            "request_id": 1,
            "initialized": True
        }
        
        print(f"✅ MCP Server '{server_name}' 준비 완료")
        return process
    
    async def start_all_servers(self):
        """모든 MCP Server 시작"""
        servers = {
            "classroom": self.mcp_dir / "classroom-mcp/server.py",
            "notice": self.mcp_dir / "notice-mcp/server.py",
            "meal": self.mcp_dir / "meal-mcp/server.py",          # 추가
            "library": self.mcp_dir / "library-mcp/server.py",    # 추가
            "shuttle": self.mcp_dir / "shuttle-mcp/server.py",    # 추가
            "course": self.mcp_dir / "course-mcp/server.py",       # 추가
            "curriculum": self.mcp_dir / "curriculum-mcp/server.py"
        }
        
        for name, path in servers.items():
            if path.exists():
                try:
                    await self.start_server(name, path)
                except Exception as e:
                    print(f"❌ MCP '{name}' 시작 실패: {e}")
            else:
                print(f"⚠️  MCP '{name}' 파일 없음: {path}")
        
        print("🚀 모든 MCP Server 준비 완료")
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """MCP Tool 호출"""
        server = self.servers.get(server_name)
        if not server:
            raise ValueError(f"MCP Server '{server_name}' not running")
        
        if not server.get("initialized"):
            raise ValueError(f"MCP Server '{server_name}' not initialized")
        
        process = server["process"]
        server["request_id"] += 1
        request_id = server["request_id"]
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        print(f"🔵 MCP 요청 [{server_name}]: {json.dumps(request, ensure_ascii=False)}")
        
        try:
            process.stdin.write((json.dumps(request) + "\n").encode())
            await process.stdin.drain()
            
            response_line = await asyncio.wait_for(
                process.stdout.readline(),
                timeout=30.0
            )
            
            if not response_line:
                raise Exception(f"No response from MCP Server '{server_name}'")
            
            response_str = response_line.decode().strip()
            print(f"🟢 MCP 응답 [{server_name}]: {response_str[:300]}...")
            
            response = json.loads(response_str)
            
            if "error" in response:
                raise Exception(f"MCP error: {response['error']}")
            
            result = response.get("result")
            
            # MCP 응답 형식 파싱
            if isinstance(result, dict):
                # 새 형식: {"content": [...], "isError": false}
                content = result.get("content", [])
                if isinstance(content, list) and len(content) > 0:
                    if isinstance(content[0], dict) and content[0].get("type") == "text":
                        return content[0].get("text", "")
            elif isinstance(result, list):
                # 구 형식: [{"type":"text","text":"..."}]
                if len(result) > 0:
                    if isinstance(result[0], dict) and result[0].get("type") == "text":
                        return result[0].get("text", "")
            
            return result
            
        except asyncio.TimeoutError:
            raise Exception(f"MCP Server '{server_name}' timeout (30s)")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON from MCP '{server_name}': {e}")
    
    async def stop_all_servers(self):
        """모든 MCP Server 종료"""
        for name, server in self.servers.items():
            process = server["process"]
            try:
                process.stdin.close()
                await asyncio.wait_for(process.wait(), timeout=2.0)
            except:
                process.terminate()
                await process.wait()
            print(f"🛑 MCP Server '{name}' 종료")
        self.servers.clear()


mcp_client = MCPClient()