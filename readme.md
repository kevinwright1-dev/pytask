# pytask

A distributed task queue built in Python from scratch. Decorate any function
with `@task` and call `.delay()` to run it in the background using a pool of
worker threads. No waiting, no blocking.

Built as a portfolio project to understand how systems like Celery, Sidekiq,
and AWS SQS work under the hood.

## How it works

```
Producer calls send_email.delay("alice@example.com")
    -> @task serializes the call to JSON and pushes to broker
    -> Worker dequeues it, looks up the function, calls it
    -> Result saved to Redis or SQLite
    -> Producer checks result by task ID
```

Five components:

**@task decorator** wraps any function and gives it a `.delay()` method.

**Broker** holds tasks in a queue. Supports Redis (LPUSH/BRPOP) and a pure TCP socket fallback.

**WorkerPool** runs concurrent threads that dequeue and execute tasks.

**ResultStore** saves the status and return value of every task to Redis or SQLite.

**Retry logic** re-enqueues failed tasks with exponential backoff and jitter, and moves permanently failed tasks to a dead-letter queue.

## Quick start

```bash
pip install -e .
```

Make sure Redis is running, then:

```python
from pytask.broker.redis import RedisBroker
from pytask.task import configure, task
from pytask.broker.worker import WorkerPool

broker = RedisBroker()
configure(broker)
worker = WorkerPool(broker, num_workers=4)
worker.start()

@task
def send_email(address, subject):
    ...

task_id = send_email.delay("user@example.com", "Welcome")
worker.stop()
```

## Examples

Each example is self-contained and runnable. They demonstrate real use cases,
not toy functions.

| Example | What it shows |
|---|---|
| `ecommerce_order_pipeline.py` | Chained background tasks: charge, reserve, confirm |
| `retry_dead_letter_demo.py` | Exponential backoff, recovery, and permanent failure |
| `dashboard_flood_test.py` | 60 jobs draining live through 6 workers |
| `gil_io_vs_cpu_comparison.py` | Why threads help I/O but not CPU (GIL) |
| `io_benchmark_plot.py` | Speedup vs task count plotted as a line chart |

Run any example:

```bash
python examples/ecommerce_order_pipeline.py
```

## Project structure

```
pytask/
    pytask/
        task.py              # @task decorator and Task class
        broker/
            base.py          # abstract Broker interface (ABC)
            redis.py         # Redis backend (LPUSH / BRPOP)
            socket.py        # pure TCP socket fallback
            worker.py        # WorkerPool (ThreadPoolExecutor)
            result.py        # RedisResultStore and SQLiteResultStore
            retry.py         # exponential backoff and dead-letter queue
            dashboard.py     # Rich live terminal dashboard
    examples/
    tests/
    DEVLOG.md                # thought process, decisions, and struggles
    pyproject.toml
```

## Key design decisions

**Why two brokers?** Redis is the industry standard. The socket fallback shows
what Redis is abstracting over: a TCP server holding a list. Both implement
the same abstract interface so the worker does not care which one it uses.

**Why threads and not async?** Most real tasks are I/O bound, meaning they spend
time waiting on networks, databases, and APIs. Threads handle this well. The GIL
only hurts CPU bound work, which should use processes instead. The
`gil_io_vs_cpu_comparison.py` example demonstrates this directly.

**Why exponential backoff?** Retrying immediately when an external service is
down makes the problem worse. Waiting longer each attempt (with jitter) gives
the service time to recover and prevents the thundering herd problem.

## DEVLOG

`DEVLOG.md` documents every session: what was built, what broke, what
decisions were made and why. 

## Requirements

Python 3.10 or higher, Redis (Memurai on Windows), and the following packages:

```bash
pip install redis rich requests matplotlib
```