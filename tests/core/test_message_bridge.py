"""Smoke test for apps.backend.src.message_bridge."""

import pytest


def test_message_bridge_imports():
    """Smoke test: apps.backend.src.message_bridge imports successfully."""
    import message_bridge
    assert message_bridge is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
