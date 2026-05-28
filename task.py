import uuid
from .broker.base import Broker

_broker = None

def configure(broker):
    global _broker
    _broker = broker

class Task():
    def __init__(self, fn):
        self.fn = fn
    def delay(self, *args, **kwargs):
        task_id = str(uuid.uuid4())
        message_dict = {
            "task_id": task_id,
            "fn": self.fn.__name__,
            "args": args,
            "kwargs": kwargs
        }
        _broker.enqueue(message_dict)
        return task_id

def task(fn):
    return Task(fn)