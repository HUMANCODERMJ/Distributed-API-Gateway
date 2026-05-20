"""
Redis service module.
Handles all Redis operations including rate limiting via Lua scripts.
"""

from redis.asyncio import Redis
from typing import Tuple

from app.core.config import REDIS_HOST, REDIS_PORT, REDIS_DB
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RedisService:
    """Manages Redis connections and operations."""
    
    _client: Redis = None
    
    @classmethod
    async def get_client(cls) -> Redis:
        """
        Get or create Redis client.
        
        Returns:
            Redis async client instance
        """
        if cls._client is None:
            cls._client = Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            logger.info("Redis client initialized: %s:%s", REDIS_HOST, REDIS_PORT)
        
        return cls._client
    
    @classmethod
    async def close(cls):
        """Close Redis connection."""
        if cls._client:
            await cls._client.close()
            cls._client = None
            logger.info("Redis client closed")
    
    @staticmethod
    async def check_rate_limit(key: str, limit: int, window: int) -> Tuple[int, bool]:
        """
        Check rate limit using Redis counter with Lua script.
        Atomically increments counter and checks if limit exceeded.
        
        Args:
            key: Redis key for tracking
            limit: Maximum requests allowed
            window: Time window in seconds
        
        Returns:
            Tuple of (count, allowed) where allowed is 1 if within limit, 0 if exceeded
        """
        client = await RedisService.get_client()
        
        script = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local count = redis.call('INCR', key)
        if count == 1 then
            redis.call('EXPIRE', key, window)
        end
        local allowed = 1
        if count > limit then
            allowed = 0
        end
        return {count, allowed}
        """
        
        result = await client.eval(script, 1, key, limit, window)
        count, allowed = result[0], result[1]
        
        return count, bool(allowed)
    
    @staticmethod
    async def set_value(key: str, value: str, ttl: int = None) -> bool:
        """
        Set a key-value pair in Redis.
        
        Args:
            key: Redis key
            value: Value to set
            ttl: Time to live in seconds (optional)
        
        Returns:
            True if successful
        """
        client = await RedisService.get_client()
        await client.set(key, value, ex=ttl)
        return True
    
    @staticmethod
    async def get_value(key: str) -> str:
        """
        Get a value from Redis.
        
        Args:
            key: Redis key
        
        Returns:
            Value if exists, None otherwise
        """
        client = await RedisService.get_client()
        return await client.get(key)
