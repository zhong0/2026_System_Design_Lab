from cache.cacheInitialize import redis_connection
from config import app_config as config
from log.logTemplate import JSONLogger

logger = JSONLogger(__name__).get_logger()

CACHE_TTL = config.CACHE_TTL

class cacheOperation:
    async def get(self, code: str):
        try:
            url = await redis_connection.client.get(f"short:{code}")
            return url
        except Exception as e:
            logger.error(f"Failed to get cache: {str(e)}")
            return None

    async def set(self, code: str, original_url: str):
        try:
            await redis_connection.client.set(f"short:{code}", original_url, ex=CACHE_TTL)
            logger.info(f"Cache set for code: {code}")
            return True
        except Exception as e:
            logger.error(f"Failed to set cache: {str(e)}")
            return False

    async def delete(self, code: str):
        try:
            await redis_connection.client.delete(f"short:{code}")
            logger.info(f"Cache deleted for code: {code}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache: {str(e)}")
            return False