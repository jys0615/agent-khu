"""
FastAPI 메인 애플리케이션 - MCP 기반 (개선판)
- DB 테이블 생성: 앱 시작 시 1회 수행
- MCP 서버 자동 시작/종료: 환경변수 MCP_AUTOSTART 로 제어(기본 true)
- CORS: 환경변수 CORS_ALLOW_ORIGINS 로 제어(쉼표 구분)
- /health, /ready 엔드포인트 제공
"""
from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import engine
from . import models
from .routers import classrooms, notices, chat, auth, profiles, cache
from .mcp_client import mcp_client
from .cache import cache_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리 - DB 준비 및 MCP Server 자동 시작/종료"""
    # 1) DB 테이블 생성 (애플리케이션 시작 시 1회)
    try:
        models.Base.metadata.create_all(bind=engine)
        print("✅ DB 테이블 확인/생성 완료")
    except Exception as e:
        print(f"❌ DB 초기화 실패: {e}")
    
    # 2) Redis 연결
    try:
        await cache_manager.connect()
    except Exception as e:
        print(f"⚠️ Redis 연결 중 오류 (캐시 없이 실행): {e}")

    # 3) MCP 서버 자동 시작 (옵션)
    autostart = os.getenv("MCP_AUTOSTART", "true").lower() == "true"
    if autostart:
        print("🚀 MCP Server들 시작 중...")
        try:
            await mcp_client.start_all_servers()
        except Exception as e:
            # lazy start가 있으므로, 실패해도 앱은 계속 구동
            print(f"❌ MCP Server 시작 중 일부 실패: {e}")
    else:
        print("ℹ️ MCP_AUTOSTART=false: 서버는 필요 시 지연 기동됩니다.")

    # 애플리케이션 실행 구간
    yield

    # 4) Redis 연결 종료
    try:
        await cache_manager.disconnect()
    except Exception as e:
        print(f"⚠️ Redis 종료 중 오류: {e}")

    # 5) MCP 서버 종료
    try:
        if autostart and mcp_client.servers:
            print("🛑 MCP Server들 종료 중...")
            await mcp_client.stop_all_servers()
    except Exception as e:
        print(f"⚠️ MCP Server 종료 중 오류: {e}")


# FastAPI 앱 구성
app = FastAPI(
    title="Agent KHU - MCP Edition",
    description="경희대 MCP 기반 통합 정보 시스템",
    version="2.0.0-MCP",
    lifespan=lifespan,
)

# CORS 설정 (환경변수로 제어)
_default_origins = "http://localhost:5173,http://localhost:3000"
allowed_origins = [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", _default_origins).split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록 (기존 유지)
app.include_router(auth.router)      # 🆕 추가
app.include_router(profiles.router) 
app.include_router(classrooms.router)
app.include_router(notices.router)
app.include_router(chat.router)
app.include_router(cache.router)     # 🆕 캐시 관리


@app.get("/")
async def root():
    return {
        "message": "Agent KHU - MCP 기반 통합 정보 시스템",
        "version": "2.0.0-MCP",
        "architecture": "MCP (Model Context Protocol)",
        "mcp_autostart": os.getenv("MCP_AUTOSTART", "true"),
        "mcp_servers": list(mcp_client.servers.keys()),
    }


@app.get("/health")
async def health_check():
    cache_info = await cache_manager.get_info()
    return {
        "status": "healthy",
        "mcp_servers_running": len(mcp_client.servers),
        "servers": list(mcp_client.servers.keys()),
        "cache": cache_info,
    }


@app.get("/ready")
async def ready():
    """간단한 준비 상태 확인: 서버 프로세스 레지스트리에 접근 가능한지만 확인"""
    return {
        "ready": True,
        "known_mcp": list(mcp_client.server_paths.keys()),
        "running": list(mcp_client.servers.keys()),
    }