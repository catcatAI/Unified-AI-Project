"""Smoke test for apps.backend.src.cluster_hardware."""

import pytest


def test_cluster_hardware_imports():
    """Smoke test: apps.backend.src.cluster_hardware imports successfully."""
    import cluster_hardware
    assert cluster_hardware is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
