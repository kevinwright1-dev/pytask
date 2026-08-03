from unittest.mock import Mock

from pytask.broker.retry import move_to_dead_letter, retry, should_dead_letter



def test_retry_increments_attempt_by_one(monkeypatch, mock_broker, message):
    """Verify retry advances the attempt count exactly once per requeue."""
    monkeypatch.setattr("pytask.broker.retry.time.sleep", Mock())
    monkeypatch.setattr("pytask.broker.retry.random.random", Mock(return_value=0))

    retry(mock_broker, message)

    assert message["attempt"] == 1


def test_retry_enqueues_updated_message(monkeypatch, mock_broker, message):
    """Verify retry re-enqueues the same message after updating attempt count."""
    monkeypatch.setattr("pytask.broker.retry.time.sleep", Mock())
    monkeypatch.setattr("pytask.broker.retry.random.random", Mock(return_value=0))

    retry(mock_broker, message)

    mock_broker.enqueue.assert_called_once_with(
        {
            "task_id": "task-123",
            "fn": "sample_task",
            "args": (1, 2),
            "kwargs": {"scale": 3},
            "attempt": 1,
        }
    )


def test_should_dead_letter_compares_attempt_to_max_retries():
    """Verify max retry boundaries avoid off-by-one dead-letter decisions."""
    assert should_dead_letter({"attempt": 4}, max_retries=5) is False
    assert should_dead_letter({"attempt": 5}, max_retries=5) is True


def test_move_to_dead_letter_enqueues_only_when_retries_exhausted(mock_broker, message):
    """Verify only exhausted messages are moved into the dead-letter queue."""
    move_to_dead_letter(mock_broker, {**message, "attempt": 4})
    mock_broker.enqueue.assert_not_called()

    exhausted = {**message, "attempt": 5}
    move_to_dead_letter(mock_broker, exhausted)

    mock_broker.enqueue.assert_called_once_with(exhausted)


def test_move_to_dead_letter_restores_original_queue_name(mock_broker, message):
    """Verify temporary dead-letter routing does not leak into future enqueues."""
    exhausted = {**message, "attempt": 5}

    move_to_dead_letter(mock_broker, exhausted)

    assert mock_broker.queue_name == "default"
