"""Smoke test for apps.backend.src.hsp.mqtt_broker_startup."""
import pytest
import sys
from pathlib import Path

def test_mqtt_broker_startup_imports():
    """Smoke test: apps.backend.src.hsp.mqtt_broker_startup imports successfully."""
    from hsp import mqtt_broker_startup as mqtt_broker_startup
    assert mqtt_broker_startup is not None


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
