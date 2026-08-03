import uuid

from .broker.base import Broker

_broker = None
_registry = {}


def configure(broker):
    """Choose the broker that all future .delay() calls should enqueue into.

    pytask keeps this as module-level configuration so individual task
    functions do not need to know whether Redis, sockets, or another broker is
    being used. Application startup configures the broker once, then task code
    can stay focused on business logic.
    """
    global _broker
    _broker = broker

class Task():
    """Wrap a Python function with queue-aware behavior.

    The wrapper deliberately keeps two modes:

    - __call__ runs the function immediately, which is useful in tests or when
      comparing synchronous behavior against queued behavior.
    - delay creates a durable task message and returns the task id immediately.
    """

    def __init__(self, fn):

        self.fn = fn

    def __call__(self, *args, **kwargs):
        """Run the wrapped function synchronously."""
        return self.fn(*args, **kwargs)

    def delay(self, *args, **kwargs):
        """Enqueue the function call and return a task id for result lookup."""

        task_id = str(uuid.uuid4())

        message_dict = {
            "task_id": task_id,
            "fn": self.fn.__name__,
            "args": args,
            "kwargs": kwargs,
            "attempt": 0
        }
        _broker.enqueue(message_dict)
        return task_id

def task(fn):
    """Decorator that turns a function into a Task wrapper."""
    _registry[fn.__name__] = fn
    return Task(fn)
