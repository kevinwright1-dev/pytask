import time
import random

def retry(broker, message):
    """Re-enqueue a failed task after exponential backoff.

    Backoff matters because retrying immediately can make an outage worse. If a
    payment API or email service is already struggling, hammering it with
    instant retries usually creates more failures. The jitter spreads retries
    out so many failed tasks do not wake up at exactly the same second.
    """
    attempt = message["attempt"]

    time.sleep(min(2 ** attempt, 60) + random.random())

    message["attempt"] += 1
    broker.enqueue(message)

def should_dead_letter(message, max_retries=5):
    """Return True when a message has exhausted its retry budget."""

    return message["attempt"] >= max_retries


def move_to_dead_letter(broker, message):
    """Move an exhausted message into the dead_letter queue."""

    if should_dead_letter(message):

        original = broker.queue_name
        broker.queue_name = "dead_letter"
        broker.enqueue(message)
        broker.queue_name = original


    
    
