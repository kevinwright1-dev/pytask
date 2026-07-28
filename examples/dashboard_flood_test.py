"""Flood the queue and watch the Dashboard table drain live.

Run with:
    python examples/dashboard_flood_test.py

This demonstrates operational visibility. A queue is most useful when you can
see whether workers are keeping up, whether pending work is draining, and
whether anything has landed in the dead-letter queue.
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


QUEUE = "default"

broker = RedisBroker(queue_name=QUEUE)
configure(broker)
results = RedisResultStore()


@task
def generate_thumbnail(image_name, size="512x512"):
    # Thumbnailing, PDF rendering, and video transcoding are good queue jobs:
    # they are small, repeatable, and slow enough that you do not want them in
    # a request/response path.
    time.sleep(0.2)
    return f"{image_name} rendered at {size}"


def wait_for_all(task_ids, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline:
        finished = [task_id for task_id in task_ids if results.get_result(task_id)]
        if len(finished) == len(task_ids):
            return
        time.sleep(0.1)
    raise TimeoutError("Timed out waiting for the flood test to drain")


def main():
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

        # Dashboard.start() is intentionally infinite for a real terminal
        # monitor. For an example script, we use the same make_table() method
        # inside a bounded Rich Live loop so the script exits cleanly.
        with Live(dashboard.make_table(), refresh_per_second=4) as live:
            while True:
                live.update(dashboard.make_table())
                if broker.r.llen(QUEUE) == 0:
                    break
                time.sleep(0.25)

        wait_for_all(task_ids)
        elapsed = time.time() - started

        print(f"\nAfter: 60 jobs completed in {elapsed:.2f}s with 6 workers.")
        print("Value: the Dashboard makes backlog and dead-letter counts visible while work runs.")

    finally:
        worker.stop()
        worker.result.r.close()
        if "dashboard" in locals():
            dashboard.r.close()
        if task_ids:
            results.r.delete(*task_ids)
        broker.r.delete(QUEUE, "dead_letter")
        results.r.close()
        broker.close()


if __name__ == "__main__":
    main()
