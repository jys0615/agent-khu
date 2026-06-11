"""
Notice MCP Server — FastMCP + Streamable HTTP (Phase 2)
공지사항 검색 및 크롤링
"""
import os
import sys
from pathlib import Path

from fastmcp import FastMCP

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import service  # noqa: E402

PORT = int(os.getenv("PORT", "8102"))
mcp = FastMCP("notice-mcp")


@mcp.tool()
async def get_latest_notices(department: str = "소프트웨어융합학과", limit: int = 5) -> dict:
    """학과별 최신 공지사항 조회

    Args:
        department: 학과명 또는 코드 (기본값: 소프트웨어융합학과)
        limit: 조회할 공지 수 (기본값: 5)
    """
    _, result = service.list_latest_notices(department, limit)
    return result


@mcp.tool()
async def search_notices(query: str, limit: int = 5, department: str = "") -> dict:
    """공지사항 키워드 검색

    Args:
        query: 검색 키워드
        limit: 최대 결과 수 (기본값: 5)
        department: 학과 필터 (비워두면 전체 검색)
    """
    result = service.search_notices(query, limit, department or None)
    return result


@mcp.tool()
async def crawl_fresh_notices(
    department: str = "소프트웨어융합학과",
    limit: int = 20,
    keyword: str = "",
) -> dict:
    """학과 공지 실시간 크롤링 (키워드 필터 지원)

    Args:
        department: 학과명 (기본값: 소프트웨어융합학과)
        limit: 크롤링할 최대 공지 수
        keyword: 필터링 키워드 (비워두면 전체)
    """
    result = service.crawl_and_persist(department, limit, keyword or None)
    return result


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=PORT, stateless_http=True)
