"""
FastAPI 메인 애플리케이션 - MCP 기반 (Lazy Start) + 자동 스케줄링
"""
from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import engine
from . import models
from .routers import classrooms, notices, chat, auth, profiles, cache, curriculum
from .mcp_client import mcp_client
from .cache import cache_manager
from .observability import obs_logger
from .scheduler import start_scheduler, shutdown_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리"""
    # 1) DB 테이블 생성
    try:
        models.Base.metadata.create_all(bind=engine)
        print("✅ DB 테이블 확인/생성 완료")
    except Exception as e:
        print(f"❌ DB 초기화 실패: {e}")
    
    # 2) Redis 연결
    try:
        await cache_manager.connect()
    except Exception as e:
        print(f"⚠️ Redis 연결 중 오류: {e}")
    
    # 3) Elasticsearch 연결
    try:
        await obs_logger.initialize()
    except Exception as e:
        print(f"⚠️ Elasticsearch 연결 중 오류: {e}")

    # 4) MCP 서버는 lazy start
    print("ℹ️ MCP 서버는 첫 tool 호출 시 자동으로 시작됩니다.")
    
    # 5) 백그라운드 스케줄러 시작
    try:
        start_scheduler()
    except Exception as e:
        print(f"⚠️ 스케줄러 시작 중 오류: {e}")

    # 6) MCP 서버 콜드스타트 완화: 가벼운 워밍업 (비차단)
    try:
        import asyncio as _asyncio
        async def _warmup_curriculum():
            try:
                # 최신 연도로 졸업요건 한 번 호출해 서버 기동 및 캐시 생성
                await mcp_client.call_tool(
                    "curriculum", "get_requirements", {"program": "KHU-CSE", "year": "latest"}, timeout=10.0, retries=1
                )
                print("🔥 MCP 워밍업: curriculum.get_requirements 완료")
            except Exception as _e:
                print(f"ℹ️ MCP 워밍업 스킵 (무시 가능): {_e}")

        # 이벤트 루프에 비동기 태스크로 등록
        _asyncio.create_task(_warmup_curriculum())
    except Exception as e:
        print(f"ℹ️ MCP 워밍업 태스크 생성 실패 (무시 가능): {e}")

    yield

    # 종료
    try:
        await obs_logger.close()
    except Exception as e:
        print(f"⚠️ Elasticsearch 종료 중 오류: {e}")

    try:
        await cache_manager.disconnect()
    except Exception as e:
        print(f"⚠️ Redis 종료 중 오류: {e}")
    
    # 스케줄러 종료
    try:
        shutdown_scheduler()
    except Exception as e:
        print(f"⚠️ 스케줄러 종료 중 오류: {e}")


app = FastAPI(
    title="Agent KHU - MCP Edition with Observability",
    description="경희대 MCP 기반 통합 정보 시스템",
    version="2.1.0-MCP+Observability",
    lifespan=lifespan,
)

# CORS
_default_origins = "http://localhost:5173,http://localhost:3000"
allowed_origins = [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", _default_origins).split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
    
    return health_status


@app.get("/ready")
async def ready():
    """준비 상태 확인"""
    return {
        "ready": True,
        "mcp_mode": "lazy_start",
        "mcp_servers_available": list(mcp_client.server_params.keys()),
    }
