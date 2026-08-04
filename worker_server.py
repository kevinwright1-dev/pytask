from pytask.broker.redis import RedisBroker
from pytask.broker.worker import WorkerPool
from pytask.task import configure
import time

# importing these files triggers @task decorators and registers all tasks
import examples.ecommerce_order_pipeline
import examples.dashboard_flood_test
import examples.gil_io_vs_cpu_comparison
import examples.io_benchmark_plot
import examples.retry_dead_letter_demo
import examples.basic_usage

broker = RedisBroker()
configure(broker)
worker = WorkerPool(broker, 9)
worker.start()
print('workers running - press Ctrl+C to stop')

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    worker.stop()
    print('workers stopped')