import os
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)

class RediceService:
    def __init__(self):
        self.db_api = os.getenv("db_info")
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        logger.info(f"Connecting to Redis at {self.redis_url}")
        self.redis_client = redis.Redis.from_url(self.redis_url, decode_responses=True)
    
    async def get(self, key):
        """Get a value from Redis asynchronously"""
        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Redis get error: {str(e)}", exc_info=True)
            return None
    
    async def set(self, key, value, ex=3600):
        """Set a value in Redis asynchronously with optional expiration"""
        try:
            await self.redis_client.set(key, value, ex=ex)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {str(e)}", exc_info=True)
            return False
    
    async def delete(self, key):
        """Delete a key from Redis asynchronously"""
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {str(e)}", exc_info=True)
            return False
