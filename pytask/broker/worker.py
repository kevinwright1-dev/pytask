import threading
from pytask.broker.retry import retry, should_dead_letter, move_to_dead_letter
from .base import Broker
from pytask.task import _registry
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
                kwargs = message["kwargs"]

                fn = _registry.get(fn_name)
                if fn is None:
                    print(f"Unknown task: {fn_name}")
                    self.result.save_result(message["task_id"], "FAILED", "Unknown task")
                    move_to_dead_letter(self.broker, message)
                    continue

                try:
                    result = fn(*args, **kwargs)
                    self.result.save_result(message["task_id"], "SUCCESS", result)
                except Exception as e:
                    if should_dead_letter(message):
                        self.result.save_result(message["task_id"], "FAILED", str(e))
                        move_to_dead_letter(self.broker, message)
                    else:
                        self.result.save_result(message["task_id"], "RETRYING", str(e))
                        retry(self.broker, message)

    def stop(self):
        """Ask all workers to exit and wait for the threads to finish."""

        self.stop_event.set()
        for t in self.threads:
            t.join()
         
         


