"""
도메인 예외 클래스 정의

FastAPI 글로벌 핸들러와 함께 사용.
모든 예외를 500으로 퉁치는 대신 의미 있는 HTTP 상태코드 반환.
"""
from __future__ import annotations


class AgentKHUError(Exception):
    """기본 도메인 예외"""


class MCPServerUnavailableError(AgentKHUError):
    """MCP 서버에 연결할 수 없을 때"""

    def __init__(self, server_name: str, detail: str = ""):
        self.server_name = server_name
        super().__init__(f"MCP 서버 '{server_name}' 응답 없음. {detail}".strip())


class MCPToolTimeoutError(AgentKHUError):
    """MCP 도구 호출 타임아웃"""

    def __init__(self, tool_name: str, timeout_sec: float):
        self.tool_name = tool_name
        self.timeout_sec = timeout_sec
        super().__init__(f"도구 '{tool_name}' 응답 시간 초과 ({timeout_sec}s)")


class RAGIndexEmptyError(AgentKHUError):
    """RAG 인덱스가 비어있어 검색 불가"""


class CacheConnectionError(AgentKHUError):
    """Redis 캐시 연결 실패"""


class InvalidQuestionError(AgentKHUError):
    """유효하지 않은 질문 (빈 문자열 등)"""
