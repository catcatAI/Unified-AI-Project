"""Smoke test for apps.backend.src.services.node_services."""
import pytest

def test_node_services_imports():
    """Smoke test: apps.backend.src.services.node_services imports successfully."""
    from services import node_services as node_services
    assert node_services.__name__ == 'services.node_services'


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
