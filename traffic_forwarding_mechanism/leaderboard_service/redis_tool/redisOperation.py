import redis
from redis_tool.redisInitialize import redis_connection
from log.logTemplate import JSONLogger

logger = JSONLogger(__name__).get_logger()

class redisOperation:
    def get_leaderboard(self, top=10):
        try:
            result = redis_connection.client.zrevrange('fortune:大吉', 0, top - 1, withscores=True)
            
            leaderboard = [
                {
                    "rank": i + 1,
                    "username": username,
                    "count": int(score)
                }
                for i, (username, score) in enumerate(result)
            ]
            
            logger.info("get leaderboard successfully")
            return leaderboard
        except Exception as e:
            logger.error(e)
            return None
        