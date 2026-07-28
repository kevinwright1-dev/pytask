# pytask

A distributed task queue built in Python. Similar to Celery but built from scratch. You decorate a function with @task and call .delay() to run it in the background using a pool of worker threads.

## What it does

Functions decorated with @task get sent to a broker which holds them in a queue. A worker pool picks them up, runs them, and saves the results. Supports Redis and a custom TCP socket server as brokers, exponential retry with dead-letter queuing for failed tasks, and a live dashboard to monitor queue state.

## How to run

Install dependencies:

```
pip install -e .
pip install redis rich
```

Make sure Redis is running, then try one of the examples:

```
python examples/ecommerce_order_pipeline.py
python examples/retry_dead_letter_demo.py
python examples/dashboard_flood_test.py
python examples/gil_io_vs_cpu_comparison.py
python examples/io_benchmark_plot.py
```

## Basic usage

```python
from pytask.broker.redis import RedisBroker
from pytask.task import configure, task

broker = RedisBroker(queue_name="default")
configure(broker)

@task
def send_email(address, subject):
    ...

send_email.delay("user@example.com", "Welcome")
```

## Project structure

```
pytask/
├── broker/
│   ├── base.py          # abstract broker class
│   ├── redis.py         # Redis broker implementation
│   ├── socket.py        # TCP socket broker and server
│   ├── result.py        # Redis and SQLite result stores
│   ├── retry.py         # retry with exponential backoff and dead-letter queue
│   └── dashboard.py     # live queue monitor using Rich
├── task.py              # Task class and @task decorator
└── examples/
    ├── ecommerce_order_pipeline.py
    ├── retry_dead_letter_demo.py
    ├── dashboard_flood_test.py
    ├── gil_io_vs_cpu_comparison.py
    └── io_benchmark_plot.py
```

## Requirements

- Python 3.10+
- Redis server running locally
- redis
- rich