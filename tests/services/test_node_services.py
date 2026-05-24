"""Smoke test for apps.backend.src.services.node_services."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "backend" / "src"))

def test_node_services_imports():
    """Smoke test: apps.backend.src.services.node_services imports successfully."""
    from services import node_services as node_services
    assert node_services.__name__ == 'services.node_services'


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
