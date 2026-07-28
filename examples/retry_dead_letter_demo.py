"""Show retry backoff and dead-letter handling for unreliable work.

Run with:
    python examples/retry_dead_letter_demo.py

WorkerPool is intentionally small and simple, so this script uses a tiny
script-local worker loop to demonstrate the public retry helpers directly:

    retry(broker, message)
    should_dead_letter(message, max_retries=...)
    move_to_dead_letter(broker, message)

The scenario is relatable: sending invoices through an external provider that
sometimes fails. One invoice recovers after retries; one exceeds the retry
limit and is moved to the dead-letter queue for human inspection.
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


QUEUE = "example:retry"

broker = RedisBroker(queue_name=QUEUE)
configure(broker)

# Make the example deterministic while still using retry()'s public formula.
random.seed(7)


@task
def send_invoice(invoice_id, customer_email, fail_until_attempt):
    """Pretend to call a flaky invoice delivery API."""
    time.sleep(0.15)
    return f"invoice {invoice_id} sent to {customer_email}"


def invoice_provider(message):
    """Raise until the message attempt reaches the scenario's threshold."""
    fail_until = message["kwargs"]["fail_until_attempt"]
    if message["attempt"] < fail_until:
        raise ConnectionError("invoice provider returned HTTP 503")
    return send_invoice(*message["args"], **message["kwargs"])


def patch_retry_sleep_for_demo(scale=0.25):
    """Keep the demo brisk while printing the real retry delay.

    retry() sleeps inside the helper. For a live demo, waiting 1 + 2 + 4 + 8
    seconds is understandable but a little tedious, so we scale the actual
    sleep while still showing the backoff value the library calculated.
    """
    original_sleep = retry_module.time.sleep

    def scaled_sleep(seconds):
        print(f"    retry() calculated {seconds:.2f}s backoff; sleeping {seconds * scale:.2f}s for demo")
        original_sleep(seconds * scale)

    retry_module.time.sleep = scaled_sleep
    return original_sleep


def main():
    broker.r.delete(QUEUE, "dead_letter")
    original_sleep = patch_retry_sleep_for_demo()

    task_ids = [
        send_invoice.delay("INV-100", "sam@example.com", fail_until_attempt=2),
        send_invoice.delay("INV-999", "ops@example.com", fail_until_attempt=99),
    ]

    print("\nRetry and dead-letter demo")
    print("Before: two invoice jobs are queued. One will recover; one will keep failing.")

    completed = {}
    max_retries = 5

    try:
        while len(completed) < 1 or broker.r.llen("dead_letter") == 0:
            message = broker.dequeue(timeout=2)
            if message is None:
                continue

            task_id = message["task_id"]
            label = message["args"][0]
            print(f"\nProcessing {label} attempt {message['attempt']}")

            try:
                completed[task_id] = invoice_provider(message)
                print(f"  success: {completed[task_id]}")
            except Exception as exc:
                print(f"  failure: {exc}")

                # should_dead_letter accepts the retry policy, so this script can
                # make the cutoff explicit in its output.
                if should_dead_letter(message, max_retries=max_retries):
                    print(f"  exceeded {max_retries} retries; moving {label} to dead_letter")

                    # move_to_dead_letter currently uses the library default of
                    # five attempts. Because max_retries is also five here, the
                    # public helper performs the final queue move for us.
                    move_to_dead_letter(broker, message)
                else:
                    print("  retrying with exponential backoff plus jitter")
                    retry(broker, message)

        print("\nAfter:")
        print(f"  completed jobs: {len(completed)}")
        print(f"  dead-letter jobs: {broker.r.llen('dead_letter')}")
        print("Value: transient failures get another chance, permanent failures are preserved.")

    finally:
        retry_module.time.sleep = original_sleep
        broker.r.delete(QUEUE, "dead_letter")
        broker.close()


if __name__ == "__main__":
    main()
