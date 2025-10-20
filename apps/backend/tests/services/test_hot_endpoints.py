import pytest
from fastapi.testclient import TestClient

from apps.backend.src.services.main_api_server import app


_ = @pytest.mark.timeout(10)
def test_hot_status_endpoint_basic_structure() -> None:
    """
    Basic smoke test for /api/v1/hot/status.
    Verifies the endpoint is available and returns the expected high-level keys.
    """
    with TestClient(app) as client:
        resp = client.get("/api/v1/hot/status")
        assert resp.status_code == 200
        data = resp.json()
        # Top-level keys
        for key in ["draining", "services_initialized", "hsp", "mcp", "metrics"]:
            assert key in data, f"Missing key in response: {key}"
        # Metrics sub-keys (best-effort presence)
        metrics = data.get("metrics", {})
        for subkey in ["hsp", "mcp", "learning", "memory", "lis"]:
            assert subkey in metrics, f"Missing metrics subkey: {subkey}"
        # Types (non-strict due to best-effort semantics)
            assert isinstance(data["services_initialized"], dict)
            assert isinstance(metrics, dict)
