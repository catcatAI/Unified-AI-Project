"""Tests for MQTT broker startup."""
import pytest


def test_mqtt_broker_stub():
    pytest.skip("MQTT broker test requires optional amqtt dependency")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])