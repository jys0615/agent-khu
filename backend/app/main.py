"""
FastAPI 메인 애플리케이션
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from . import models
from .routers import chat, classrooms, notices

# 데이터베이스 테이블 생성
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Agent KHU API",
    description="경희대 소프트웨어융합대학 AI 챗봇 API",
    version="1.0.0"
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
app.include_router(chat.router)
app.include_router(classrooms.router)
app.include_router(notices.router)


@app.get("/")
async def root():
    """API 루트"""
    return {
        "message": "Agent KHU API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/chat",
            "classrooms": "/api/classrooms",
            "notices": "/api/notices"
        }
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy"}