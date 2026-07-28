import socket
import time

import pytest

from pytask.broker.redis import RedisBroker
from pytask.broker.socket import SocketBroker, start_server


@pytest.fixture
def redis_broker(monkeypatch):
    """Provide a RedisBroker backed by fakeredis, skipping if unavailable."""
    fakeredis = pytest.importorskip(
        "fakeredis",
        reason="fakeredis is required for isolated Redis broker tests; otherwise use a real Redis instance.",
    )
    fake_server = fakeredis.FakeServer()

    def fake_redis(*args, **kwargs):
        return fakeredis.FakeRedis(server=fake_server)

    monkeypatch.setattr("pytask.broker.redis.redis.Redis", fake_redis)
    broker = RedisBroker(queue_name="pytest-default")
    yield broker
    broker.r.flushall()
    broker.close()


def test_redis_broker_enqueue_dequeue_round_trips_message(redis_broker, message):
    """Verify RedisBroker JSON-serializes and deserializes every message field."""
    redis_broker.enqueue(message)

    result = redis_broker.dequeue(timeout=1)

    assert result == {
        **message,
        "args": list(message["args"]),
    }


def test_redis_broker_dequeue_returns_none_when_empty(redis_broker):
    """Verify RedisBroker returns None instead of blocking forever on empty queues."""
    assert redis_broker.dequeue(timeout=1) is None


@pytest.fixture(scope="session")
def socket_server():
    """Start the TCP fallback server once for SocketBroker integration tests."""
    start_server()
    deadline = time.monotonic() + 2
    while True:
        try:
            with socket.create_connection(("localhost", 9999), timeout=0.1):
                return
        except OSError:
            if time.monotonic() >= deadline:
                pytest.fail("SocketBroker test server did not start")
            time.sleep(0.01)


@pytest.fixture
def socket_broker(socket_server):
    """Provide a fresh SocketBroker client connected to the local test server."""
    broker = SocketBroker(host="localhost", port=9999)
    yield broker
    broker.close()


def test_socket_broker_enqueue_dequeue_round_trips_message(socket_broker, message):
    """Verify SocketBroker can push and pop a JSON task message over TCP."""
    socket_broker.enqueue(message)

    result = socket_broker.dequeue(timeout=1)

    assert result == {
        **message,
        "args": list(message["args"]),
    }


def test_socket_broker_dequeue_returns_none_when_empty(socket_broker):
    """Verify SocketBroker maps the EMPTY sentinel to None for idle workers."""
    assert socket_broker.dequeue(timeout=1) is None
