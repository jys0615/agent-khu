"""
Redis 기반 캐시 매니저
- 비동기 Redis 클라이언트
- JSON 직렬화/역직렬화
- TTL 설정 가능
- 키 패턴 기반 삭제
"""
import os
import json
import hashlib
from typing import Any, Optional, List
from redis import asyncio as aioredis
from redis.exceptions import RedisError


class CacheManager:
    """Redis 캐시 매니저"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self._connected = False
    
    async def connect(self):
        """Redis 연결"""
        if self._connected:
            return
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5.0,
                socket_connect_timeout=5.0
            )
            # 연결 테스트
            await self.redis.ping()
            self._connected = True
            print(f"✅ Redis 연결 성공: {redis_url}")
        except RedisError as e:
            print(f"⚠️ Redis 연결 실패: {e}")
            print("⚠️ 캐시 없이 계속 실행됩니다.")
            self.redis = None
            self._connected = False
    
    async def disconnect(self):
        """Redis 연결 종료"""
        if self.redis:
            await self.redis.close()
            self._connected = False
            print("✅ Redis 연결 종료")
    
    def _make_key(self, prefix: str, **kwargs) -> str:
        """캐시 키 생성 (일관된 해싱)"""
        # kwargs를 정렬하여 일관된 키 생성
        sorted_items = sorted(kwargs.items())
        key_parts = [prefix] + [f"{k}:{v}" for k, v in sorted_items]
        key_str = ":".join(str(p) for p in key_parts)
        
        # 긴 키는 해시 처리
        if len(key_str) > 200:
            hash_suffix = hashlib.md5(key_str.encode()).hexdigest()[:16]
            return f"{prefix}:{hash_suffix}"
        
        return key_str
    
    async def get(self, key: str) -> Optional[Any]:
        """캐시 조회"""
        if not self._connected or not self.redis:
            return None
        
        try:
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except (RedisError, json.JSONDecodeError) as e:
            print(f"⚠️ 캐시 조회 실패 ({key}): {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """캐시 저장 (TTL: 초 단위)"""
        if not self._connected or not self.redis:
            return False
        
        try:
            serialized = json.dumps(value, ensure_ascii=False)
            await self.redis.setex(key, ttl, serialized)
            return True
        except (RedisError, TypeError, ValueError) as e:
            print(f"⚠️ 캐시 저장 실패 ({key}): {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """캐시 삭제"""
        if not self._connected or not self.redis:
            return False
        
        try:
            await self.redis.delete(key)
            return True
        except RedisError as e:
            print(f"⚠️ 캐시 삭제 실패 ({key}): {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """패턴 매칭으로 여러 키 삭제"""
        if not self._connected or not self.redis:
            return 0
        
        try:
            # SCAN을 사용하여 키 찾기 (메모리 효율적)
            deleted = 0
            async for key in self.redis.scan_iter(match=pattern, count=100):
                await self.redis.delete(key)
                deleted += 1
            return deleted
        except RedisError as e:
            print(f"⚠️ 패턴 삭제 실패 ({pattern}): {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """캐시 존재 확인"""
        if not self._connected or not self.redis:
            return False
        
        try:
            return await self.redis.exists(key) > 0
        except RedisError:
            return False
    
    async def get_ttl(self, key: str) -> int:
        """캐시 남은 시간 조회 (초)"""
        if not self._connected or not self.redis:
            return -1
        
        try:
            return await self.redis.ttl(key)
        except RedisError:
            return -1
    
    async def keys(self, pattern: str = "*") -> List[str]:
        """패턴 매칭으로 키 목록 조회"""
        if not self._connected or not self.redis:
            return []
        
        try:
            keys = []
            async for key in self.redis.scan_iter(match=pattern, count=100):
                keys.append(key)
            return keys
        except RedisError as e:
            print(f"⚠️ 키 조회 실패 ({pattern}): {e}")
            return []
    
    async def clear_all(self) -> bool:
        """모든 캐시 삭제 (주의!)"""
        if not self._connected or not self.redis:
            return False
        
        try:
            await self.redis.flushdb()
            print("✅ 모든 캐시 삭제됨")
            return True
        except RedisError as e:
            print(f"⚠️ 캐시 전체 삭제 실패: {e}")
            return False
    
    async def get_info(self) -> dict:
        """Redis 서버 정보 조회"""
        if not self._connected or not self.redis:
            return {"connected": False}
        
        try:
            info = await self.redis.info()
            return {
                "connected": True,
                "version": info.get("redis_version"),
                "used_memory_human": info.get("used_memory_human"),
                "total_keys": await self.redis.dbsize(),
            }
        except RedisError as e:
            return {"connected": False, "error": str(e)}


# 싱글톤 인스턴스
cache_manager = CacheManager()