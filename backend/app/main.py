"""
FastAPI 메인 애플리케이션 - MCP 기반 (Lazy Start) + 자동 스케줄링
"""
from __future__ import annotations

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from .config import get_settings, configure_logging
from .exceptions import AgentKHUError, MCPServerUnavailableError, MCPToolTimeoutError
from .database import engine
from . import models
from .routers import classrooms, notices, chat, auth, profiles, cache, curriculum
from .mcp_client import mcp_client
from .cache import cache_manager
from .observability import obs_logger
from .rag_agent import get_rag_agent
from .scheduler import start_scheduler, shutdown_scheduler

settings = get_settings()
configure_logging(settings.log_level)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리"""
    # 1) DB 테이블 생성
    try:
        models.Base.metadata.create_all(bind=engine)
        log.info("DB 테이블 확인/생성 완료")
    except Exception as e:
        log.error("DB 초기화 실패: %s", e)

    # 2) Redis 연결
    try:
        await cache_manager.connect()
    except Exception as e:
        log.warning("Redis 연결 중 오류: %s", e)

    # 3) Elasticsearch 연결 (Observability)
    try:
        await obs_logger.initialize()
    except Exception as e:
        log.warning("Elasticsearch 연결 중 오류: %s", e)

    # 4) RAG Agent 초기화
    try:
        await get_rag_agent().initialize()
    except Exception as e:
        log.warning("RAG Agent 초기화 중 오류: %s", e)

    # 5) MCP 서버는 lazy start
    log.info("MCP 서버는 첫 tool 호출 시 자동으로 시작됩니다.")

    # 6) 백그라운드 스케줄러 시작
    try:
        start_scheduler()
    except Exception as e:
        log.warning("스케줄러 시작 중 오류: %s", e)

    # 7) MCP 서버 콜드스타트 완화: 가벼운 워밍업 (비차단)
    try:
        import asyncio as _asyncio

        async def _warmup():
            # curriculum — 졸업요건 조회 빈도가 높음
            try:
                await mcp_client.call_tool(
                    "curriculum", "get_requirements",
                    {"program": "KHU-CSE", "year": "latest"},
                    timeout=15.0, retries=1,
                )
                log.info("MCP 워밍업: curriculum.get_requirements 완료")
            except Exception as _e:
                log.debug("MCP 워밍업 스킵 (curriculum): %s", _e)

            # classroom — 첫 호출 시 DB 연결 초기화로 콜드스타트 길어짐
            try:
                await mcp_client.call_tool(
                    "classroom", "search_classroom",
                    {"query": "전101"},
                    timeout=30.0, retries=0,
                )
                log.info("MCP 워밍업: classroom.search_classroom 완료")
            except Exception as _e:
                log.debug("MCP 워밍업 스킵 (classroom): %s", _e)

        _asyncio.create_task(_warmup())
    except Exception as e:
        log.debug("MCP 워밍업 태스크 생성 실패 (무시 가능): %s", e)

    yield

    # 종료
    try:
        await obs_logger.close()
    except Exception as e:
        log.warning("Elasticsearch 종료 중 오류: %s", e)

    try:
        await get_rag_agent().close()
    except Exception as e:
        log.warning("RAG Agent 종료 중 오류: %s", e)

    try:
        await cache_manager.disconnect()
    except Exception as e:
        log.warning("Redis 종료 중 오류: %s", e)

    try:
        shutdown_scheduler()
    except Exception as e:
        log.warning("스케줄러 종료 중 오류: %s", e)


app = FastAPI(
    title="Agent KHU - MCP Edition with Observability",
    description="경희대 MCP 기반 통합 정보 시스템",
    version="2.1.0-MCP+Observability",
    lifespan=lifespan,
)

# ── 글로벌 예외 핸들러 ────────────────────────────────────────────

@app.exception_handler(MCPServerUnavailableError)
async def mcp_unavailable_handler(request: Request, exc: MCPServerUnavailableError):
    log.error("MCP 서버 사용 불가: %s", exc.server_name)
    return JSONResponse(status_code=503, content={"error": str(exc), "code": "MCP_UNAVAILABLE"})


@app.exception_handler(MCPToolTimeoutError)
async def mcp_timeout_handler(request: Request, exc: MCPToolTimeoutError):
    log.warning("MCP 도구 타임아웃: %s (%.1fs)", exc.tool_name, exc.timeout_sec)
    return JSONResponse(status_code=504, content={"error": str(exc), "code": "MCP_TIMEOUT"})


@app.exception_handler(AgentKHUError)
async def agent_error_handler(request: Request, exc: AgentKHUError):
    log.error("도메인 오류: %s", exc)
    return JSONResponse(status_code=500, content={"error": str(exc), "code": "AGENT_ERROR"})


# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터
app.include_router(auth.router)
app.include_router(profiles.router) 
app.include_router(classrooms.router)
app.include_router(notices.router)
app.include_router(chat.router)
app.include_router(cache.router)
app.include_router(curriculum.router)


@app.get("/")
async def root():
    return {
        "message": "Agent KHU - MCP 기반 통합 정보 시스템",
        "version": "2.1.0-MCP+Observability",
        "architecture": "MCP (Model Context Protocol)",
        "features": ["Caching", "Observability", "Question Classification"],
        "mcp_mode": "lazy_start",
        "mcp_servers_available": list(mcp_client.server_params.keys()),
    }


@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    health_status = {
        "status": "healthy",
        "version": "2.1.0-MCP+Observability",
        "architecture": "MCP (Model Context Protocol)",
        "features": ["Caching", "Observability", "Question Classification"],
        "mcp_mode": "lazy_start",
        "mcp_servers_available": list(mcp_client.server_params.keys()),
    }
    
    # Cache 상태
    try:
        cache_info = await cache_manager.get_cache_info()
        health_status["cache"] = cache_info
    except Exception as e:
        health_status["cache"] = {"error": str(e)}
    
    # Observability 상태
    health_status["observability"] = {
        "elasticsearch_enabled": obs_logger.enabled,
        "elasticsearch_url": obs_logger.es_url if obs_logger.enabled else None
    }

    # RAG 상태
    try:
        rag_stats = await get_rag_agent().get_stats()
        health_status["rag"] = rag_stats
    except Exception as e:
        health_status["rag"] = {"error": str(e)}

    return health_status


@app.get("/ready")
async def ready():
    """준비 상태 확인"""
    return {
        "ready": True,
        "mcp_mode": "lazy_start",
        "mcp_servers_available": list(mcp_client.server_params.keys()),
    }
