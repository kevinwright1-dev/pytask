import threading
import sys
from .base import Broker
from pytask.broker.result import RedisResultStore


class WorkerPool:
    def __init__(self, broker, num_workers):
        self.broker = broker
        self.num_workers = num_workers
        self.stop_event = threading.Event()
        self.threads = []
        self.result = RedisResultStore()
    def start(self):
        for i in range(self.num_workers):
            t = threading.Thread(target=self._run)
            t.start()
            self.threads.append(t)
    def _run(self):
        while not self.stop_event.is_set():
            message = self.broker.dequeue(timeout=2)
            if message is not None:
                fn_name = message["fn"]
                args = message["args"]
                kwargs = message ["kwargs"]
                module = sys.modules["__main__"]
                fn = getattr(module, fn_name)
                result = fn(*args, **kwargs)
                self.result.save_result(message["task_id"], "SUCCESS", result)
    def stop(self):
        self.stop_event.set()
        for t in self.threads:
            t.join()
         
         


