import itertools
from unittest.mock import Mock

import pytest


@pytest.fixture
def message():
    """Provide a representative task message shared by broker and worker tests."""
    return {
        "task_id": "task-123",
        "fn": "sample_task",
        "args": (1, 2),
        "kwargs": {"scale": 3},
        "attempt": 0,
    }


@pytest.fixture
def mock_broker():
    """Provide a mock broker for tests that should not use network services."""
    broker = Mock()
    broker.queue_name = "default"
    return broker


@pytest.fixture
def task_ids(monkeypatch):
    """Make generated task ids deterministic so message assertions stay focused."""
    ids = (f"task-{i}" for i in itertools.count(1))
    monkeypatch.setattr("pytask.task.uuid.uuid4", lambda: next(ids))
    return ids
