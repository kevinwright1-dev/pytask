import json
import os
import redis
from .base import Broker

class RedisBroker(Broker):
    """Redis-backed broker using a Redis list as the queue.

    Redis lists are a good fit for a small task queue because LPUSH can enqueue
    quickly and BRPOP can let workers wait efficiently until work arrives.
    """

    def __init__(self, queue_name="default"):

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.r = redis.Redis.from_url(redis_url)
        self.queue_name = queue_name

    def enqueue(self, message, queue_name=None):
        """Serialize and push one task message onto the requested queue."""
        message_json = json.dumps(message)
        target_queue = queue_name or self.queue_name
        self.r.lpush(target_queue, message_json)

    def dequeue(self, timeout):
        """Block for work until timeout, then return a decoded message or None."""

        result = self.r.brpop(self.queue_name,timeout)
        if result is None:
            return None
        else:
            return json.loads(result[1])

    def close(self):
        """Close the Redis connection owned by this broker."""
        self.r.close()
