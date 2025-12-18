"""
MCP 클라이언트 - 공식 MCP SDK 사용 (안정판)
매 tool 호출마다 세션 생성/종료 → Context 관리 문제 완전 해결
"""
from __future__ import annotations

import os
import sys
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """공식 MCP SDK를 사용하는 클라이언트 (안정적 구현)"""

    def __init__(self) -> None:
        self.server_paths: Dict[str, Path] = {}
        self.server_params: Dict[str, StdioServerParameters] = {}
        # 서버별 호출 직렬화를 위한 락 (프로세스 스폰 경합 방지)
        self._locks: Dict[str, asyncio.Lock] = {}

        # MCP 서버 경로 해상도
        env_root = os.getenv("MCP_ROOT")
        candidates = []

        if env_root:
            p = Path(env_root)
            if p.exists():
                candidates.append(p)

        # 프로젝트 루트 기준
        try:
            repo_root = Path(__file__).resolve().parents[2]
            candidates.append(repo_root / "mcp-servers")
        except Exception:
            pass

        # 실행 위치 기준
        try:
            cwd = Path(os.getcwd()).resolve()
            candidates.append((cwd / "../mcp-servers").resolve())
            candidates.append(cwd / "mcp-servers")
        except Exception:
            pass

        # 폴백
        candidates.append(Path.home() / "Desktop/agent-khu/mcp-servers")

        root: Optional[Path] = None
        for c in candidates:
            try:
                if c.exists():
                    root = c.resolve()
                    break
            except Exception:
                continue

        if root is None:
            root = candidates[-1]
            print(f"⚠️ MCP 디렉터리를 찾지 못했습니다: {root}")

        self.mcp_dir = root
        print(f"🔧 MCP_DIR = {self.mcp_dir}")

        # 기본 서버 경로 등록
        self._register_default_servers()

    def _register_default_servers(self) -> None:
        """기본 MCP 서버 경로 등록"""
        paths = {
            "classroom": self.mcp_dir / "classroom-mcp/server.py",
            "notice": self.mcp_dir / "notice-mcp/server.py",
            "meal": self.mcp_dir / "meal-mcp/server.py",
            "library": self.mcp_dir / "library-mcp/server.py",
            "course": self.mcp_dir / "course-mcp/server.py",
            "curriculum": self.mcp_dir / "curriculum-mcp/server.py",
        }
        self.server_paths.update(paths)
        
        # 환경변수 준비 (DATABASE_URL 포함)
        env = os.environ.copy()
        # Ensure MCP subprocesses can import the backend `app` package
        try:
            backend_root = Path(__file__).resolve().parents[1]  # .../backend
            existing_pp = env.get("PYTHONPATH", "")
            pp_parts = [p for p in existing_pp.split(os.pathsep) if p]
            if str(backend_root) not in pp_parts:
                pp_parts.append(str(backend_root))
            env["PYTHONPATH"] = os.pathsep.join(pp_parts) if pp_parts else str(backend_root)
            # Avoid stdout buffering surprises
            env.setdefault("PYTHONUNBUFFERED", "1")
        except Exception:
            pass
        
        # 실행할 파이썬 인터프리터 (현재 프로세스와 동일한 인터프리터 사용)
        python_cmd = sys.executable or "python3"

        # StdioServerParameters 미리 생성
        for name, path in paths.items():
            if path.exists():
                self.server_params[name] = StdioServerParameters(
                    command=python_cmd,
                    args=[str(path)],
                    env=env  # ✅ 환경변수 전달
                )
                # 각 서버별 Lock 준비
                self._locks.setdefault(name, asyncio.Lock())

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        *,
        timeout: float = 5.0,
        retries: int = 1
    ) -> Any:
        """
        MCP Tool 호출 (매번 세션 생성/종료)
        
        이 방식은:
        1. Context가 같은 함수에서 생성/종료됨 ✅
        2. Task 불일치 문제 없음 ✅
        3. MCP 표준 완전 준수 ✅
        """
        
        params = self.server_params.get(server_name)
        if not params:
            raise ValueError(f"등록되지 않은 MCP 서버: {server_name}")

        attempt = 0
        last_error = None
        while True:
            try:
                # 서버별 직렬화로 프로세스 스폰 경합 방지
                lock = self._locks.setdefault(server_name, asyncio.Lock())
                async with lock:
                    # stdio_client context: 프로세스 생성/종료
                    async with stdio_client(params) as (read, write):
                        # ClientSession context: 세션 초기화/종료
                        async with ClientSession(read, write) as session:
                            # 초기화 (타임아웃 적용) — 콜드스타트 대비 여유를 더 줌
                            init_timeout = max(timeout, 12.0)
                            await asyncio.wait_for(session.initialize(), timeout=init_timeout)

                            # Preflight: list_tools로 서버 준비 상태 확인 (무시 가능)
                            try:
                                await asyncio.wait_for(session.list_tools(), timeout=5.0)
                            except Exception:
                                # 일부 서버는 list_tools를 느리게 반환할 수 있음 — 실패해도 계속 진행
                                pass

                            # Tool 호출 (타임아웃 적용)
                            call_timeout = max(timeout, 10.0)
                            result = await asyncio.wait_for(
                                session.call_tool(tool_name, arguments), timeout=call_timeout
                            )

                            # 결과 파싱
                            parsed_result = self._parse_result(result)

                            return parsed_result
            
            # 여기서 context 자동 종료 ✅
            
            except Exception as e:
                attempt += 1
                last_error = e
                error_type = type(e).__name__
                error_msg = str(e)
                
                # ExceptionGroup 내부 예외 추출
                if hasattr(e, 'exceptions'):
                    inner_errors = [str(ex) for ex in e.exceptions[:3]]  # 첫 3개만
                    error_msg = f"{error_msg} | Inner: {', '.join(inner_errors)}"
                
                print(f"❌ MCP Tool 호출 실패({attempt}/{retries+1}): {server_name}.{tool_name} - {error_type}: {error_msg}", flush=True)
                
                if attempt > retries:
                    raise Exception(f"MCP error after {retries+1} attempts: {error_type} - {error_msg}")
                # 에러 유형 기반 백오프 조정
                backoff = 0.5 * attempt
                if "handler is closed" in error_msg or "TCPTransport closed" in error_msg:
                    backoff = max(backoff, 1.0)
                await asyncio.sleep(backoff)

    def _parse_result(self, result: Any) -> Any:
        """MCP 결과 파싱"""
        if hasattr(result, 'content') and result.content:
            # content가 리스트인 경우
            if isinstance(result.content, list):
                texts = []
                for item in result.content:
                    if hasattr(item, 'text'):
                        texts.append(item.text)
                    elif isinstance(item, dict) and 'text' in item:
                        texts.append(item['text'])
                
                if texts:
                    combined = "\n".join(texts)
                    # JSON 파싱 시도
                    try:
                        import json
                        return json.loads(combined)
                    except:
                        return combined
            
            # content가 단일 객체인 경우
            if hasattr(result.content, 'text'):
                try:
                    import json
                    return json.loads(result.content.text)
                except:
                    return result.content.text
        
        return result

    async def stop_all_servers(self):
        """
        서버 종료 (실제로는 할 일 없음)
        각 call_tool에서 이미 context가 종료되었음
        """
        print("🛑 MCP Client 종료")

    # Convenience wrappers for common servers/tools
    async def meal_get_today(self, meal_type: str = "lunch") -> Any:
        return await self.call_tool("meal", "get_today_meal", {"meal_type": meal_type})

    async def meal_scrape_weekly(self) -> Any:
        return await self.call_tool("meal", "scrape_weekly_meal", {})

    async def library_info(self, campus: str = "seoul") -> Any:
        return await self.call_tool("library", "get_library_info", {"campus": campus})

    async def library_seats(self, username: str, password: str, campus: str = "seoul") -> Any:
        return await self.call_tool("library", "get_seat_availability", {
            "username": username, "password": password, "campus": campus
        })

    async def library_reserve(self, username: str, password: str, room: str, seat_number: str | None = None) -> Any:
        payload = {"username": username, "password": password, "room": room}
        if seat_number:
            payload["seat_number"] = seat_number
        return await self.call_tool("library", "reserve_seat", payload)

    async def course_search(self, department: str = "소프트웨어융합학과", keyword: str | None = None) -> Any:
        payload = {"department": department}
        if keyword:
            payload["keyword"] = keyword
        return await self.call_tool("course", "search_courses", payload)

    async def course_professor(self, professor: str) -> Any:
        return await self.call_tool("course", "get_professor_courses", {"professor": professor})

    async def course_by_code(self, code: str) -> Any:
        return await self.call_tool("course", "get_course_by_code", {"code": code})


# 전역 인스턴스
mcp_client = MCPClient()
