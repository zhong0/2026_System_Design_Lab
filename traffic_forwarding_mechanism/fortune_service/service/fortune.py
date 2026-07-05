import random
from redis_tool.redisOperation import redisOperation

class fortuneSvc:
    def __init__(self):
        self.fortune_type = ["大吉", "吉", "中吉", "小吉", "末吉", "凶"]
        self.fortune_weight = [10, 20, 20, 20, 20, 10]
        self.redis_op = redisOperation()
    
    def random_draw(self, username):
        fortune_type = random.choices(self.fortune_type, weights=self.fortune_weight , k=1)[0]
        if fortune_type == "大吉":
            result = self.redis_op.set_sorted(f'fortune:{fortune_type}', username)
            if not result:
                return None
        return fortune_type
