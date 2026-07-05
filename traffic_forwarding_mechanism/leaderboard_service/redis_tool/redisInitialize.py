import redis
from config import app_config as config
from log.logTemplate import JSONLogger

logger = JSONLogger(__name__).get_logger()

class redisInitialize:
    def __init__(self, host, port, db=0, max_connections=10):
        self.client = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            max_connections=max_connections,
            decode_responses=True
        )
    
    def connect(self):
        try:
            self.client = redis.Redis(connection_pool=self.client)
            self.client.ping()
            logger.info("Connect to redis successfully.")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
    
    def disconnect(self):
        if self.client:
            self.client.close()
            logger.info(f"Disconnect to MongoDB Successfully")

redis_connection = redisInitialize(config.REDIS_IP, config.REDIS_PORT)