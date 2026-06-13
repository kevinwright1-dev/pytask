import time
import random

def retry(broker, message):
    attempt = message["attempt"]
    time.sleep(min(2 ** attempt, 60) + random.random())
    message["attempt"] += 1
    broker.enqueue(message)

def should_dead_letter(message, max_retries=5):
    return message["attempt"] >= max_retries


def move_to_dead_letter(broker, message):
    if should_dead_letter(message):
        original = broker.queue_name
        broker.queue_name = "dead_letter"
        broker.enqueue(message)
        broker.queue_name = original


    
    
