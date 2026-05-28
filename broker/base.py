from abc import ABC, abstractmethod

class Broker(ABC):

    @abstractmethod
    def enqueue(self, message):
        """Must take a message(dict) as an arg"""
        ...
    @abstractmethod
    def dequeue(self, timeout):
        """Takes a timeout in seconds and returns a dict or None"""
        ...
    @abstractmethod
    def close(self):
        """takes no arguments"""
        ...