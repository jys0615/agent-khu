from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from .database import engine, Base
from .routers import chat, notices  # 🆕 notices 추가

load_dotenv()

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Agent KHU API",
    description="경희대학교 강의실 안내 AI Agent API",
    version="0.2.0"  # 버전 업
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(chat.router)
app.include_router(notices.router)  # 🆕


@app.get("/")
async def root():
    return {
        "message": "Agent KHU API",
        "version": "0.2.0",
        "features": ["classroom", "instagram_notices"],  # 🆕
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}