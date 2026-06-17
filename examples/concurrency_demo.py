from pytask.task import task, configure
from pytask.broker.redis import RedisBroker
from pytask.broker.worker import WorkerPool
from pytask.broker.result import RedisResultStore
import time
import requests

broker = RedisBroker()
configure(broker)
result_store = RedisResultStore()
worker = WorkerPool(broker, 5)
worker.start()

urls = [
    "https://httpbin.org/delay/2",
    "https://httpbin.org/delay/2",
    "https://httpbin.org/delay/2",
    "https://httpbin.org/delay/2",
    "https://httpbin.org/delay/2",
]

@task
def download_url(link):
    start = time.time()
    r = requests.get(link)
    end = time.time()
    elapsed = end - start
    return elapsed, link

sequential_time = 0
concurrent_time = 0
seq_start = time.time()
for url in urls:
    download_url(url)
seq_end = time.time()
sequential_time = seq_end - seq_start

conc_start = time.time()
id1 = download_url.delay(urls[0])
id2 = download_url.delay(urls[1])
id3 = download_url.delay(urls[2])
id4 = download_url.delay(urls[3])
id5 = download_url.delay(urls[4])

time.sleep(5)

conc_end = time.time()
concurrent_time = conc_end - conc_start

worker.stop()

print(f"Sequential Time: {sequential_time:.2f}s")
print(f"Concurrent Time: {concurrent_time:.2f}s")
