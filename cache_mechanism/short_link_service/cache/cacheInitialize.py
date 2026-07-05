import redis.asyncio as aioredis
from config import app_config as config
from log.logTemplate import JSONLogger

logger = JSONLogger(__name__).get_logger()

class cacheInitialize:
    def __init__(self, host, port, password, db=0, max_connections=10):
        self.pool = aioredis.ConnectionPool(
            host=host,
            port=port,
            password=password,
            db=db,
            max_connections=max_connections,
            decode_responses=True
        )
        self.client = None
    
    async def connect(self):
        try:
            self.client = aioredis.Redis(connection_pool=self.pool)
            await self.client.ping()
            logger.info("Connect to redis successfully.")
        except aioredis.ConnectionError as e:
            logger.error(f"Failed to connect to redis: {str(e)}")
    
    async def disconnect(self):
        if self.client:
            await self.client.aclose()
            logger.info("Disconnect to redis successfully.")

redis_connection = cacheInitialize(config.REDIS_IP, config.REDIS_PORT, config.REDIS_PWD)