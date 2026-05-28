"""Smoke test for apps.backend.src.services.resource_awareness_service."""
import pytest

def test_resource_awareness_service_imports():
    """Smoke test: apps.backend.src.services.resource_awareness_service imports successfully."""
    from services import resource_awareness_service as resource_awareness_service
    assert resource_awareness_service.__name__ == 'services.resource_awareness_service'


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
