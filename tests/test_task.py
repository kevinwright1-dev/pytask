from unittest.mock import Mock

from pytask.task import configure, task


def test_task_decorator_preserves_direct_call_behavior():
    """Verify @task returns a callable wrapper so synchronous use still works."""

    @task
    def add(left, right):
        return left + right

    assert add(2, 3) == 5


def test_delay_returns_string_task_id(mock_broker, task_ids):
    """Verify delay returns a string id callers can use to track task results."""

    configure(mock_broker)

    @task
    def add(left, right):
        return left + right

    task_id = add.delay(2, 3)

    assert isinstance(task_id, str)
    assert task_id == "task-1"


def test_delay_enqueues_correctly_structured_message(mock_broker, task_ids):
    """Verify delay emits the expected message keys and values for workers."""

    configure(mock_broker)

    @task
    def format_name(first, last=None):
        return f"{first} {last}"

    task_id = format_name.delay("Ada", last="Lovelace")

    mock_broker.enqueue.assert_called_once_with(
        {
            "task_id": task_id,
            "fn": "format_name",
            "args": ("Ada",),
            "kwargs": {"last": "Lovelace"},
            "attempt": 0,
        }
    )


def test_configure_changes_broker_used_by_future_delay_calls(task_ids):
    """Verify configure updates the module-level broker used by later delays."""

    first_broker = Mock()
    second_broker = Mock()

    @task
    def ping():
        return "pong"

    configure(first_broker)
    ping.delay()
    configure(second_broker)
    ping.delay()

    first_broker.enqueue.assert_called_once()
    second_broker.enqueue.assert_called_once()
