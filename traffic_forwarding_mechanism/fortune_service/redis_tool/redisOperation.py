import redis
from redis_tool.redisInitialize import redis_connection
from config import app_config as config
from log.logTemplate import JSONLogger

logger = JSONLogger(__name__).get_logger()

class redisOperation:
    def set_sorted(self, key, username):
        try:
            redis_connection.client.zincrby(key, 1, username)
            logger.info("save drawing result successfully")
            return True
        except Exception as e:
            logger.error(e)
            return False
        