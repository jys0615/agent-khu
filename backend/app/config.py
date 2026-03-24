"""
애플리케이션 설정 관리 (pydantic-settings)

환경변수 누락 시 서버 시작 단계에서 즉시 실패.
os.getenv() 산재 패턴 대신 단일 Settings 인스턴스 사용.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── 필수 ──────────────────────────────────────────────────────
    anthropic_api_key: str

    # ── DB ───────────────────────────────────────────────────────
    database_url: str = "postgresql://postgres:postgres@localhost:5432/agent_khu"

    # ── Redis ────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379"

    # ── Elasticsearch ────────────────────────────────────────────
    elasticsearch_url: str = "http://localhost:9200"

    # ── CORS ─────────────────────────────────────────────────────
    cors_allow_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins(self) -> List[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    # ── MCP ──────────────────────────────────────────────────────
    mcp_root: str = ""

    # ── 로깅 ──────────────────────────────────────────────────────
    log_level: str = "INFO"

    # ── RAG ──────────────────────────────────────────────────────
    rag_score_threshold: float = 1.5
    rag_top_k: int = 3

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"log_level must be one of {valid}")
        return upper


def configure_logging(level: str = "INFO") -> None:
    """애플리케이션 전체 로깅 설정"""
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # 외부 라이브러리 노이즈 억제
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("elasticsearch").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)


@lru_cache
def get_settings() -> Settings:
    """싱글톤 Settings 인스턴스"""
    return Settings()
