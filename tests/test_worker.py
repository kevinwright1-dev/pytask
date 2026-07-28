import sys
import time
from unittest.mock import Mock

from pytask.broker.worker import WorkerPool


class FakeResultStore:
    def __init__(self):
        self.save_result = Mock()


def test_worker_pool_start_spins_up_configured_thread_count(monkeypatch, mock_broker):
    """Verify start creates and starts exactly num_workers worker threads."""
    started_threads = []

    class FakeThread:
        def __init__(self, target):
            self.target = target

        def start(self):
            started_threads.append(self)

    monkeypatch.setattr("pytask.broker.worker.threading.Thread", FakeThread)
    monkeypatch.setattr("pytask.broker.worker.RedisResultStore", FakeResultStore)
    pool = WorkerPool(mock_broker, num_workers=3)

    pool.start()

    assert len(pool.threads) == 3
    assert len(started_threads) == 3
    assert all(thread.target == pool._run for thread in pool.threads)


def test_worker_dequeues_and_calls_main_function(monkeypatch, message):
    """Verify a worker resolves the named function and passes args and kwargs."""
    called = Mock(return_value=6)
    monkeypatch.setattr(sys.modules["__main__"], "sample_task", called, raising=False)
    monkeypatch.setattr("pytask.broker.worker.RedisResultStore", FakeResultStore)

    class OneMessageBroker:
        def __init__(self):
            self.pool = None
            self.messages = [message]

        def dequeue(self, timeout):
            if self.messages:
                return self.messages.pop(0)
            self.pool.stop_event.set()
            return None

    broker = OneMessageBroker()
    pool = WorkerPool(broker, num_workers=1)
    broker.pool = pool

    pool._run()

    called.assert_called_once_with(1, 2, scale=3)


def test_worker_stop_joins_all_threads(mock_broker, monkeypatch):
    """Verify stop signals shutdown and joins every worker thread cleanly."""
    monkeypatch.setattr("pytask.broker.worker.RedisResultStore", FakeResultStore)
    pool = WorkerPool(mock_broker, num_workers=2)
    pool.threads = [Mock(), Mock()]

    pool.stop()

    assert pool.stop_event.is_set()
    for thread in pool.threads:
        thread.join.assert_called_once_with()


def test_worker_start_stop_has_no_hanging_threads(monkeypatch):
    """Verify an idle worker can be stopped without leaving a live thread."""
    monkeypatch.setattr("pytask.broker.worker.RedisResultStore", FakeResultStore)

    class IdleBroker:
        def dequeue(self, timeout):
            time.sleep(0.01)
            return None

    pool = WorkerPool(IdleBroker(), num_workers=1)
    pool.start()
    pool.stop()

    assert all(not thread.is_alive() for thread in pool.threads)


def test_worker_saves_successful_result(monkeypatch, message):
    """Verify successful task execution is persisted through the result store."""
    monkeypatch.setattr(sys.modules["__main__"], "sample_task", lambda *args, **kwargs: 6, raising=False)
    monkeypatch.setattr("pytask.broker.worker.RedisResultStore", FakeResultStore)

    class OneMessageBroker:
        def __init__(self):
            self.pool = None
            self.messages = [message]

        def dequeue(self, timeout):
            if self.messages:
                return self.messages.pop(0)
            self.pool.stop_event.set()
            return None

    broker = OneMessageBroker()
    pool = WorkerPool(broker, num_workers=1)
    broker.pool = pool

    pool._run()

    pool.result.save_result.assert_called_once_with("task-123", "SUCCESS", 6)
