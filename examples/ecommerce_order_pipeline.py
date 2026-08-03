"""Run an e-commerce order pipeline as chained background tasks.

Run with:
    python examples/ecommerce_order_pipeline.py

This example shows a common queue use case: the customer-facing request only
needs to enqueue work quickly, while slow operational steps run in the
background. Each task enqueues the next step, forming a simple pipeline:

    charge payment -> reserve inventory -> send confirmation
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
def charge_payment(order):
    time.sleep(0.35)
    print(f"  charged ${order['total']:.2f} for order {order['id']}")
    return order


@task
def reserve_inventory(order):
    time.sleep(0.25)
    print(f"  reserved {len(order['items'])} item(s) for order {order['id']}")
    return order


@task
def send_confirmation(order):
    time.sleep(0.2)
    message = f"confirmation sent to {order['email']} for order {order['id']}"
    print(f"  {message}")
    return message


def main():
    QUEUE = "example:ecommerce"
    broker = RedisBroker(queue_name=QUEUE)
    configure(broker)
    results = RedisResultStore()
    task_ids = []

    def wait_for_result(task_id, timeout=10):
        deadline = time.time() + timeout
        while time.time() < deadline:
            result = results.get_result(task_id)
            if result is not None:
                return result
            time.sleep(0.1)
        raise TimeoutError(f"Timed out waiting for {task_id}")

    orders = [
        {"id": "A1001", "email": "maya@example.com", "items": ["tea", "mug"], "total": 34.50},
        {"id": "A1002", "email": "noah@example.com", "items": ["beans"], "total": 18.00},
        {"id": "A1003", "email": "li@example.com", "items": ["grinder", "filters"], "total": 89.99},
        {"id": "A1004", "email": "ava@example.com", "items": ["kettle"], "total": 45.25},
    ]

    broker.r.delete(QUEUE, "dead_letter")
    worker = WorkerPool(broker, num_workers=3)
    worker.start()

    try:
        print("\nE-commerce pipeline demo")
        print("Before: checkout would run payment, inventory, and email in one slow request.")

        sync_start = time.time()
        for order in orders:
            time.sleep(0.35)
            time.sleep(0.25)
            time.sleep(0.2)
        sync_elapsed = time.time() - sync_start

        print(f"\nSynchronous comparison: {len(orders)} orders took {sync_elapsed:.2f}s.")
        print("Now enqueue the same batch and let three workers process the pipeline.")

        async_start = time.time()
        for order in orders:
            task_id = charge_payment.delay(order)
            task_ids.append(task_id)
        enqueue_elapsed = time.time() - async_start

        print(f"After: customer-facing checkout enqueued {len(orders)} orders in {enqueue_elapsed:.3f}s.")
        print("Workers continue the chained payment -> inventory -> confirmation flow:\n")

        for task_id in task_ids:
            wait_for_result(task_id)

        total_background_elapsed = time.time() - async_start
        print(f"\nBackground pipeline finished in {total_background_elapsed:.2f}s.")
        print("Value: the request path stayed fast while workers handled slow side effects.")

    finally:
        worker.stop()
        broker.r.delete(QUEUE, "dead_letter")
        results.r.close()
        broker.close()


if __name__ == "__main__":
    main()