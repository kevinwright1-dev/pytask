"""Basic usage demo showing the core pytask API.

Run with:
    python examples/basic_usage.py
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pytask.broker.redis import RedisBroker
from pytask.broker.result import RedisResultStore
from pytask.broker.worker import WorkerPool
from pytask.task import configure, task


@task
def add(a, b):
    return int(a) + int(b)

@task
def subtract(a, b):
    return int(a) - int(b)

@task
def multiply(a, b):
    return int(a) * int(b)

@task
def slow_task(seconds):
    time.sleep(int(seconds))
    return f"finished after {seconds}s"


def main():
    broker = RedisBroker()
    configure(broker)
    result_store = RedisResultStore()
    worker = WorkerPool(broker, 3)
    worker.start()

    id1 = add.delay(6, 3)
    id2 = subtract.delay(6, 3)
    id3 = multiply.delay(6, 3)

    time.sleep(3)

    print(result_store.get_result(id1))
    print(result_store.get_result(id2))
    print(result_store.get_result(id3))

    worker.stop()


if __name__ == "__main__":
    main()