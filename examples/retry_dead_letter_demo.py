"""Show retry backoff and dead-letter handling for unreliable work.

Run with:
    python examples/retry_dead_letter_demo.py
"""

import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytask.broker.retry as retry_module
from pytask.broker.redis import RedisBroker
from pytask.broker.retry import move_to_dead_letter, retry, should_dead_letter
from pytask.task import configure, task


@task
def send_invoice(invoice_id, customer_email, fail_until_attempt):
    time.sleep(0.15)
    return f"invoice {invoice_id} sent to {customer_email}"


def invoice_provider(message):
    fail_until = message["kwargs"]["fail_until_attempt"]
    if message["attempt"] < fail_until:
        raise ConnectionError("invoice provider returned HTTP 503")
    return send_invoice(*message["args"], **message["kwargs"])


def patch_retry_sleep_for_demo(scale=0.25):
    original_sleep = retry_module.time.sleep

    def scaled_sleep(seconds):
        print(f"    retry() calculated {seconds:.2f}s backoff; sleeping {seconds * scale:.2f}s for demo")
        original_sleep(seconds * scale)

    retry_module.time.sleep = scaled_sleep
    return original_sleep


def main():
    QUEUE = "example:retry"
    broker = RedisBroker(queue_name=QUEUE)
    configure(broker)
    random.seed(7)

    broker.r.delete(QUEUE, "dead_letter")
    original_sleep = patch_retry_sleep_for_demo()