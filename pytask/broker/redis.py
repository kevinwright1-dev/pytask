import json
import redis
from .base import Broker

class RedisBroker(Broker):
    """Redis-backed broker using a Redis list as the queue.

    Redis lists are a good fit for a small task queue because LPUSH can enqueue
    quickly and BRPOP can let workers wait efficiently until work arrives.
    """

    def __init__(self, host="localhost", port=6379, queue_name="default"):

        self.r = redis.Redis(host=host, port=port)
        self.queue_name = queue_name

    def enqueue(self, message):
        """Serialize and push one task message onto the configured queue."""


        message_json = json.dumps(message)
        self.r.lpush(self.queue_name, message_json)

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
