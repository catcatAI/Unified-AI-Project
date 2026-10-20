"""
ANGELA-MATRIX: [L4] [β] [B] [L3]
The dashboard's pet panel must show the REAL digital-life state.

The panel used to render a *local* simulation: an in-memory object in the
Next.js API route that decayed on its own and answered pet/feed/play/rest
with hard-coded deltas. The numbers on screen were unrelated to the system
they claimed to describe.

These tests pin both halves: the backend reports the real state (and names
the source), and every backend path the dashboard proxies exists.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_API = ROOT / "apps" / "web-dashboard" / "src" / "pages" / "api"


def _backend_paths() -> set:
    from services.main_api_server import app

    return set(app.openapi()["paths"].keys())


def _proxied_paths() -> list:
    """Every backend path the dashboard proxies."""
    found = []
    for path in DASHBOARD_API.rglob("*.ts"):
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"\$\{BACKEND\}(/api/v1/[A-Za-z0-9_/{}\-.]*)", text):
            found.append(match.group(1))
    return sorted(set(found))


class TestDashboardProxiesRealEndpoints:
    def test_every_proxied_backend_path_exists(self):
        paths = _backend_paths()
        missing = [p for p in _proxied_paths() if p not in paths]
        assert not missing, f"the dashboard proxies endpoints that do not exist: {missing}"

    def test_the_proxied_set_is_not_empty(self):
        """A guard that passes because nothing matched would be a false green."""
        assert len(_proxied_paths()) >= 5


class TestPetPanel:
    def test_the_pet_endpoint_reports_the_real_state(self):
        import asyncio

        from api.routes.system_routes import system_pet_state

        result = asyncio.run(system_pet_state())
        assert result["source"] in ("state_matrix", "unavailable")
        for field in ("happiness", "hunger", "energy", "health"):
            assert 0.0 <= float(result[field]) <= 1.0

    def test_an_interaction_changes_the_real_matrix(self):
        import asyncio

        from api.routes.chat_routes import _get_state_matrix
        from api.routes.system_routes import system_pet_interact, system_pet_state

        matrix = _get_state_matrix()
        before = float(matrix.gamma.values.get("happiness", 0.5))
        asyncio.run(system_pet_interact({"action": "pet"}))
        after = float(matrix.gamma.values.get("happiness", 0.5))
        assert after != before, "the interaction did not reach the state matrix"
        # The reported state must agree with the matrix.
        reported = asyncio.run(system_pet_state())
        assert abs(float(reported["happiness"]) - after) < 1e-6

    def test_an_unknown_action_is_rejected(self):
        import asyncio

        from api.routes.system_routes import system_pet_interact
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as excinfo:
            asyncio.run(system_pet_interact({"action": "not_an_action"}))
        assert excinfo.value.status_code == 400


class TestTheDashboardNoLongerSimulates:
    def test_the_pet_route_proxies_the_backend(self):
        text = (DASHBOARD_API / "pet.ts").read_text(encoding="utf-8")
        assert "/api/v1/system/pet" in text
        assert "simulated" in text  # the fallback is labelled, not silent

    def test_the_interaction_route_proxies_the_backend(self):
        text = (DASHBOARD_API / "pet" / "interact.ts").read_text(encoding="utf-8")
        assert "/api/v1/system/pet/interact" in text
        # The old implementation mutated a local object; that is gone.
        assert "petState" not in text
