"""Compare I/O-bound and CPU-bound work under pytask worker threads.

Run with:
    python examples/gil_io_vs_cpu_comparison.py
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
def call_shipping_rate_api(shipment_id, latency=0.3):
    time.sleep(latency)
    return f"rate quote ready for shipment {shipment_id}"


@task
def score_fraud_risk(order_id, iterations=1_200_000):
    score = 0
    for i in range(iterations):
        score = (score + (i * 31) % 97) % 10_000
    return {"order_id": order_id, "score": score}


def wait_for_results(task_ids, results, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if all(results.get_result(task_id) for task_id in task_ids):
            return
        time.sleep(0.05)
    raise TimeoutError("Timed out waiting for worker results")


def run_sequential(task_obj, count):
    start = time.time()
    for item in range(count):
        task_obj(item)
    return time.time() - start


def run_with_queue(task_obj, count, results):
    task_ids = []
    start = time.time()
    for item in range(count):
        task_ids.append(task_obj.delay(item))
    wait_for_results(task_ids, results)
    elapsed = time.time() - start
    results.r.delete(*task_ids)
    return elapsed


def main():
    QUEUE = "example:gil-comparison"
    broker = RedisBroker(queue_name=QUEUE)
    configure(broker)
    results = RedisResultStore()

    count = 8
    broker.r.delete(QUEUE, "dead_letter")
    worker = WorkerPool(broker, num_workers=4)
    worker.start()

    try:
        print("\nI/O-bound vs CPU-bound comparison")
        print("Before: both workloads run sequentially.")
        print("After: the same workloads run through four pytask worker threads.\n")

        io_sequential = run_sequential(call_shipping_rate_api, count)
        io_queue = run_with_queue(call_shipping_rate_api, count, results)

        cpu_sequential = run_sequential(score_fraud_risk, count)
        cpu_queue = run_with_queue(score_fraud_risk, count, results)

        print("workload       | sequential | pytask workers | takeaway")
        print("---------------|------------|----------------|-------------------------------")
        print(f"I/O-bound API  | {io_sequential:>10.2f}s | {io_queue:>14.2f}s | queue overhead dominates for small batches")
        print(f"CPU-bound risk | {cpu_sequential:>10.2f}s | {cpu_queue:>14.2f}s | GIL limits thread speedup")

        print("Value: pytask shines at scale. For small batches, serialization overhead")
        print("       makes it slower. For larger I/O workloads, parallelism wins.")

    finally:
        worker.stop()
        worker.result.r.close()
        broker.r.delete(QUEUE, "dead_letter")
        results.r.close()
        broker.close()


if __name__ == "__main__":
    main()