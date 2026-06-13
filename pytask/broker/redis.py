import json
import redis
from .base import Broker

class RedisBroker(Broker):

    def __init__(self, host="localhost", port=6379, queue_name="default"):
        self.r = redis.Redis(host=host, port=port)
        self.queue_name = queue_name

    def enqueue(self, message):
        message_json = json.dumps(message)
        self.r.lpush(self.queue_name, message_json)

    def dequeue(self, timeout):
        result = self.r.brpop(self.queue_name,timeout)
        if result is None:
            return None
        else:
            return json.loads(result[1])

    def close(self):
        self.r.close()