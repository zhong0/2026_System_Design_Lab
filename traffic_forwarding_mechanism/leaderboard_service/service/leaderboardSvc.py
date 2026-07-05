import random
from redis_tool.redisOperation import redisOperation

class leaderboardSvc:
    def __init__(self):
        self.redis_op = redisOperation()
    
    def leaderboard_retrieval(self):
        result = self.redis_op.get_leaderboard()
        if result is None:
            return None
        else:
            return result
