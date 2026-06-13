import time
import random
from .base import Broker
attempt = 0
def retry(broker, message):
    time.sleep(min(2 ** attempt, 60) + random.random())
    broker.enqueue(message)
    attempt += 1
    
