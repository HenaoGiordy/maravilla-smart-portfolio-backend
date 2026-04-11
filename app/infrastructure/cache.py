import json
from typing import Any, Optional

import redis.asyncio as redis

from app.config.settings import get_settings

settings = get_settings()


class RedisCache:
    """Redis cache client with async support."""

    _instance: Optional[redis.Redis] = None

    @classmethod
    async def get_instance(cls) -> redis.Redis:
        """Get or create Redis connection."""
        if cls._instance is None:
            cls._instance = await redis.from_url(settings.redis_url)
        return cls._instance

    @staticmethod
    async def get(key: str) -> Optional[Any]:
        """Get value from cache."""
        cache = await RedisCache.get_instance()
        value = await cache.get(key)
        if value:
            return json.loads(value)
        return None

    @staticmethod
    async def set(key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with optional TTL."""
        cache = await RedisCache.get_instance()
        if ttl is None:
            ttl = settings.cache_ttl_seconds
        await cache.setex(key, ttl, json.dumps(value))
        return True

    @staticmethod
    async def delete(key: str) -> bool:
        """Delete key from cache."""
        cache = await RedisCache.get_instance()
        await cache.delete(key)
        return True

    @staticmethod
    async def flush() -> bool:
        """Flush all cache."""
        cache = await RedisCache.get_instance()
        await cache.flushdb()
        return True

    @staticmethod
    async def close():
        """Close Redis connection."""
        if RedisCache._instance:
            await RedisCache._instance.close()
