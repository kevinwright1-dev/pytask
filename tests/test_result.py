import pytest

from pytask.broker.result import RedisResultStore, SQLiteResultStore


@pytest.fixture
def sqlite_store(tmp_path, monkeypatch):
    """Create a SQLiteResultStore in a temporary working directory."""
    monkeypatch.chdir(tmp_path)
    store = SQLiteResultStore()
    yield store
    store.conn.close()


def test_sqlite_result_store_round_trips_saved_result(sqlite_store):
    """Verify SQLiteResultStore can persist and retrieve a completed task."""
    sqlite_store.save_result("task-1", "SUCCESS", "done")

    assert sqlite_store.get_result("task-1") == {
        "task_id": "task-1",
        "status": "SUCCESS",
        "value": "done",
    }


def test_sqlite_result_store_returns_none_for_missing_task(sqlite_store):
    """Verify missing task ids return None so callers can distinguish no result."""
    assert sqlite_store.get_result("missing") is None


def test_sqlite_result_store_replaces_existing_task_id(sqlite_store):
    """Verify INSERT OR REPLACE updates an existing task instead of erroring."""
    sqlite_store.save_result("task-1", "PENDING", "old")
    sqlite_store.save_result("task-1", "SUCCESS", "new")

    assert sqlite_store.get_result("task-1") == {
        "task_id": "task-1",
        "status": "SUCCESS",
        "value": "new",
    }


@pytest.fixture
def redis_result_store(monkeypatch):
    """Provide a RedisResultStore backed by fakeredis for isolated JSON tests."""
    fakeredis = pytest.importorskip(
        "fakeredis",
        reason="fakeredis is required for isolated Redis result tests; otherwise use a real Redis instance.",
    )
    fake_server = fakeredis.FakeServer()

    def fake_redis(*args, **kwargs):
        return fakeredis.FakeRedis(server=fake_server)

    monkeypatch.setattr("pytask.broker.result.redis.Redis", fake_redis)
    store = RedisResultStore()
    yield store
    store.r.flushall()
    store.r.close()


@pytest.mark.parametrize(
    ("task_id", "value"),
    [
        ("task-string", "done"),
        ("task-number", 42),
        ("task-object", [{"name": "Ada"}, {"count": 2}]),
    ],
)
def test_redis_result_store_round_trips_json_values(redis_result_store, task_id, value):
    """Verify RedisResultStore JSON-serializes non-string result payloads."""
    redis_result_store.save_result(task_id, "SUCCESS", value)

    assert redis_result_store.get_result(task_id) == {
        "status": "SUCCESS",
        "value": value,
    }
