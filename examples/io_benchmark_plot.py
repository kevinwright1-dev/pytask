"""Benchmark sequential I/O work against pytask workers and plot the speedup.

Run with:
    python examples/io_benchmark_plot.py

The point of this benchmark is consistency. Instead of one lucky timing, it
runs increasing workloads and plots both lines:

    x-axis: number of simulated I/O tasks
    y-axis: elapsed seconds
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


QUEUE = "example:io-benchmark"
PLOT_PATH = Path(__file__).with_name("io_benchmark.png")

broker = RedisBroker(queue_name=QUEUE)
configure(broker)
results = RedisResultStore()


@task
def fetch_customer_profile(customer_id, latency=0.35):
    # Simulate network I/O that workers can overlap.
    time.sleep(latency)
    return {"customer_id": customer_id, "tier": "standard"}


def run_sequential(count):
    start = time.time()
    for customer_id in range(count):
        fetch_customer_profile(customer_id)
    return time.time() - start


def wait_for_results(task_ids, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if all(results.get_result(task_id) for task_id in task_ids):
            return
        time.sleep(0.05)
    raise TimeoutError("Timed out waiting for benchmark tasks")


def run_with_queue(count):
    task_ids = []
    start = time.time()
    for customer_id in range(count):
        task_ids.append(fetch_customer_profile.delay(customer_id))
    wait_for_results(task_ids)
    elapsed = time.time() - start
    results.r.delete(*task_ids)
    return elapsed


def plot_results(workloads, sequential_times, queue_times):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("\nmatplotlib is not installed, so no PNG chart was written.")
        print("Install it with `pip install matplotlib` and rerun to create the plot.")
        return

    plt.figure(figsize=(8, 5))
    plt.plot(workloads, sequential_times, marker="o", label="Sequential")
    plt.plot(workloads, queue_times, marker="o", label="pytask workers")
    plt.xlabel("Number of simulated I/O tasks")
    plt.ylabel("Seconds")
    plt.title("Sequential vs pytask workers for I/O-bound work")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOT_PATH)
    print(f"\nChart written to {PLOT_PATH}")


def main():
    workloads = [2, 4, 6, 8, 10]
    sequential_times = []
    queue_times = []

    broker.r.delete(QUEUE, "dead_letter")
    worker = WorkerPool(broker, num_workers=5)
    worker.start()

    try:
        print("\nI/O benchmark with increasing workloads")
        print("Before: each customer profile lookup waits on an external service.")
        print("After: workers overlap those waits, so elapsed time grows more slowly.\n")
        print("tasks | sequential | pytask workers | speedup")
        print("------|------------|----------------|--------")

        for count in workloads:
            broker.r.delete(QUEUE)
            seq = run_sequential(count)
            queued = run_with_queue(count)
            sequential_times.append(seq)
            queue_times.append(queued)
            print(f"{count:>5} | {seq:>10.2f}s | {queued:>14.2f}s | {seq / queued:>6.2f}x")

        plot_results(workloads, sequential_times, queue_times)
        print("Value: the line chart shows the speedup holding as load increases.")

    finally:
        worker.stop()
        worker.result.r.close()
        broker.r.delete(QUEUE, "dead_letter")
        results.r.close()
        broker.close()


if __name__ == "__main__":
    main()
