import threading
import sys
from .base import Broker
from pytask.broker.result import RedisResultStore


class WorkerPool:
    """Run queued tasks on a fixed number of background threads.

    A WorkerPool turns queued messages back into function calls. It is best
    suited for I/O-heavy work because threads can overlap waiting on databases,
    APIs, email providers, filesystems, and other slow external services.
    """

    def __init__(self, broker, num_workers):

        self.broker = broker
        self.num_workers = num_workers
        self.stop_event = threading.Event()
        self.threads = []

        self.result = RedisResultStore()

    def start(self):
        """Start the configured number of worker threads."""

        for i in range(self.num_workers):
            t = threading.Thread(target=self._run)
            t.start()
            self.threads.append(t)

    def _run(self):
        """Worker loop: dequeue one message, execute it, persist the result."""

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
        """Ask all workers to exit and wait for the threads to finish."""

        self.stop_event.set()
        for t in self.threads:
            t.join()
         
         


