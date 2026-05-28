import pytest
from broker.base import Broker

class TestBaseBroker:
    def test_enqueue_rejects_non_dict(self, broker):
        with pytest.raises(TypeError):
            broker.enqueue("not a dict")

        with pytest.raises(TypeError):
            broker.enqueue(123)

        with pytest.raises(TypeError):
            broker.enqueue(["a", "b", "c"])
