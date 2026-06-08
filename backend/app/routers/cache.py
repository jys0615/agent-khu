"""
캐시 관리 API 엔드포인트
- 캐시 상태 조회
- 캐시 삭제 (관리자 전용)
- 캐시 통계
"""
import os
from fastapi import APIRouter, HTTPException, Header
from typing import Dict, Any, Optional
from ..cache import cache_manager

router = APIRouter(prefix="/api/cache", tags=["cache"])

# 관리자 인증 — X-Admin-Key 헤더가 환경변수 ADMIN_SECRET_KEY와 일치해야 함
_ADMIN_SECRET = os.getenv("ADMIN_SECRET_KEY", "")


def _require_admin(x_admin_key: Optional[str] = Header(default=None)) -> None:
    """캐시 삭제 엔드포인트용 관리자 인증 의존성.

    ADMIN_SECRET_KEY 환경변수가 비어 있으면 인증을 건너뜁니다 (개발 환경).
    운영 환경에서는 반드시 ADMIN_SECRET_KEY를 설정하세요.
    """
    if not _ADMIN_SECRET:
        # 개발 환경: 키 미설정 시 경고 후 허용
        import logging
        logging.getLogger(__name__).warning(
            "ADMIN_SECRET_KEY not set — cache clear endpoint is unprotected"
        )
        return
    if x_admin_key != _ADMIN_SECRET:
        raise HTTPException(
            status_code=403,
            detail="Admin access required. Provide valid X-Admin-Key header.",
        )


@router.get("/info")
async def get_cache_info() -> Dict[str, Any]:
    """Redis 캐시 정보 조회"""
    info = await cache_manager.get_info()
    
    if not info.get("connected"):
        raise HTTPException(status_code=503, detail="Cache not available")
    
    return info


@router.get("/keys")
async def get_cache_keys(pattern: str = "*") -> Dict[str, Any]:
    """캐시 키 목록 조회
    
    Args:
        pattern: Redis 패턴 (예: tool:*, classroom:*)
    """
    keys = await cache_manager.keys(pattern)
    return {
        "pattern": pattern,
        "count": len(keys),
        "keys": keys[:100]  # 최대 100개만 반환
    }


@router.delete("/clear")
async def clear_cache(
    pattern: str = "*",
    _: None = Header(default=None, include_in_schema=False),
    x_admin_key: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    """캐시 삭제 (관리자 전용)

    Args:
        pattern: 삭제할 키 패턴 (기본값: 모든 키)

    Headers:
        X-Admin-Key: 관리자 시크릿 키 (ADMIN_SECRET_KEY 환경변수)

    ⚠️ 주의: pattern="*"는 모든 캐시를 삭제합니다!
    """
    _require_admin(x_admin_key)

    if pattern == "*":
        success = await cache_manager.clear_all()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
        return {"message": "All cache cleared", "pattern": "*"}

    deleted = await cache_manager.delete_pattern(pattern)
    return {
        "message": f"Deleted {deleted} keys",
        "pattern": pattern,
        "deleted_count": deleted,
    }


@router.delete("/key/{key}")
async def delete_cache_key(key: str) -> Dict[str, Any]:
    """특정 캐시 키 삭제"""
    success = await cache_manager.delete(key)
    
    if not success:
        raise HTTPException(status_code=404, detail="Key not found or failed to delete")
    
    return {"message": f"Key '{key}' deleted"}


@router.get("/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """캐시 통계 조회"""
    info = await cache_manager.get_info()
    
    if not info.get("connected"):
        raise HTTPException(status_code=503, detail="Cache not available")
    
    # tool별 캐시 개수
    tool_keys = await cache_manager.keys("tool:*")
    tool_stats = {}
    for key in tool_keys:
        # key 형식: tool:search_classroom:hash
        parts = key.split(":")
        if len(parts) >= 2:
            tool_name = parts[1]
            tool_stats[tool_name] = tool_stats.get(tool_name, 0) + 1
    
    return {
        "redis_version": info.get("version"),
        "memory_used": info.get("used_memory_human"),
        "total_keys": info.get("total_keys"),
        "tools_cached": tool_stats,
    }