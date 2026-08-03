"""Flood the queue and watch the Dashboard table drain live.

Run with:
    python examples/dashboard_flood_test.py
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rich.live import Live

from pytask.broker.dashboard import Dashboard
from pytask.broker.redis import RedisBroker
from pytask.broker.result import RedisResultStore
from pytask.broker.worker import WorkerPool
from pytask.task import configure, task


@task
def generate_thumbnail(image_name, size="512x512"):
    time.sleep(0.2)
    return f"{image_name} rendered at {size}"


def wait_for_all(task_ids, results, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        finished = [t for t in task_ids if results.get_result(t)]
        if len(finished) == len(task_ids):
            return
        time.sleep(0.1)
    raise TimeoutError("Timed out waiting for the flood test to drain")


def main():
    QUEUE = "default"
    broker = RedisBroker(queue_name=QUEUE)
    configure(broker)
    results = RedisResultStore()

    broker.r.delete(QUEUE, "dead_letter")
    worker = WorkerPool(broker, num_workers=6)
    worker.start()

    task_ids = []

    try:
        print("\nDashboard flood test")
        print("Before: pending queue count is 0.")
        print("Enqueuing 60 image-processing jobs at once; watch the table drain.\n")

        for number in range(1, 61):
            task_ids.append(generate_thumbnail.delay(f"catalog-image-{number:03}.jpg"))

        dashboard = Dashboard(broker)
        started = time.time()

        with Live(dashboard.make_table(), refresh_per_second=4) as live:
            while True:
                live.update(dashboard.make_table())
                if broker.r.llen(QUEUE) == 0:
                    break
                time.sleep(0.25)

        wait_for_all(task_ids, results)
        elapsed = time.time() - started

        print(f"\nAfter: 60 jobs completed in {elapsed:.2f}s with 6 workers.")
        print("Value: the Dashboard makes backlog and dead-letter counts visible while work runs.")

    finally:
        worker.stop()
        worker.result.r.close()
        if task_ids:
            results.r.delete(*task_ids)
        broker.r.delete(QUEUE, "dead_letter")
        results.r.close()
        broker.close()


if __name__ == "__main__":
    main()