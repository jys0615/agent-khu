"""
FastAPI 메인 애플리케이션 - MCP 기반
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database import engine
from . import models
from .routers import classrooms, notices, chat
from .mcp_client import mcp_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리 - MCP Server 자동 시작/종료"""
    # 시작 시
    print("🚀 MCP Server들 시작 중...")
    await mcp_client.start_all_servers()
    
    yield
    
    # 종료 시
    print("🛑 MCP Server들 종료 중...")
    await mcp_client.stop_all_servers()


# 데이터베이스 테이블 생성
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Agent KHU - MCP Edition",
    description="경희대 MCP 기반 통합 정보 시스템",
    version="2.0.0-MCP",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(classrooms.router)
app.include_router(notices.router)
app.include_router(chat.router)


@app.get("/")
async def root():
    return {
        "message": "Agent KHU - MCP 기반 통합 정보 시스템",
        "version": "2.0.0-MCP",
        "architecture": "MCP (Model Context Protocol)",
        "mcp_servers": list(mcp_client.servers.keys())
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mcp_servers_running": len(mcp_client.servers),
        "servers": list(mcp_client.servers.keys())
    }