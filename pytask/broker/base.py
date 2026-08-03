from abc import ABC, abstractmethod

class Broker(ABC):
    """
    WorkerPool only depends on these three methods. That makes RedisBroker and
    SocketBroker interchangeable from the worker's point of view.
    """

    @abstractmethod
    def enqueue(self, message):
        """Put one task message onto the queue.

        The message is a plain dict produced by Task.delay(). Implementations
        decide how to serialize it.
        """
        ...

    @abstractmethod
    def dequeue(self, timeout):
        """Wait for one task message and return it, or None when idle.

        The timeout matters because workers need regular chances to notice a
        shutdown signal instead of blocking forever on an empty queue.
        """
        ...

    @abstractmethod
    def close(self):
        """Release sockets, Redis clients, or any other backend resources."""
        ...
