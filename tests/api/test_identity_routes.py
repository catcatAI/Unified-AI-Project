"""
ANGELA-MATRIX: [L4] [β] [B] [L3]
The identity API: who the user is talking to, and the rename (handover).

Covers:
- route registration (GET /identity, POST /identity/name)
- GET reports the configured default for an unnamed instance
- POST validates the name and performs the handover (name + persona state)
- POST rejects an unusable name with 400
- the rename is per user: another user keeps the default name
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps/backend/src"))


@pytest.fixture
def identity_store(tmp_path, monkeypatch):
    from core.system.config import identity

    store_path = tmp_path / "identities.json"
    monkeypatch.setattr(identity, "IDENTITY_STORE_PATH", str(store_path))
    identity.clear_cache()
    yield store_path
    identity.clear_cache()


@pytest.mark.asyncio
class TestIdentityRoutes:
    async def test_routes_are_registered(self):
        from api.routes.identity_routes import router

        paths = {r.path for r in router.routes}
        assert "/identity" in paths
        assert "/identity/name" in paths

        methods = set()
        for r in router.routes:
            if r.path == "/identity/name":
                methods.update(r.methods or set())
        assert "POST" in methods

    async def test_get_reports_the_default_for_an_unnamed_instance(self, identity_store):
        from api.routes.identity_routes import get_identity

        result = await get_identity(user_id="u1")
        assert result["ai_name"] == "Angela"
        assert result["source"] == "config"
        assert result["customized"] is False
        assert result["persona_state"] == "host"
        assert result["needs_naming"] is True
        assert result["host"] == "Lucifaella"

    async def test_post_names_the_instance_and_hands_over(self, identity_store):
        from api.routes.identity_routes import get_identity, set_identity_name

        result = await set_identity_name({"name": "小安", "user_id": "u1"}, user_id=None)
        assert result["ok"] is True
        assert result["ai_name"] == "小安"
        assert result["persona_state"] == "handover"
        assert "小安" in result["message"]

        after = await get_identity(user_id="u1")
        assert after["ai_name"] == "小安"
        assert after["source"] == "user"
        assert after["persona_state"] == "handover"
        assert after["needs_naming"] is False

    async def test_post_rejects_an_unusable_name(self, identity_store):
        from api.routes.identity_routes import set_identity_name
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as excinfo:
            await set_identity_name({"name": "   ", "user_id": "u1"}, user_id=None)
        assert excinfo.value.status_code == 400

    async def test_post_requires_a_user(self, identity_store):
        from api.routes.identity_routes import set_identity_name
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as excinfo:
            await set_identity_name({"name": "小安"}, user_id=None)
        assert excinfo.value.status_code == 400

    async def test_the_rename_is_per_user(self, identity_store):
        from api.routes.identity_routes import get_identity, set_identity_name

        await set_identity_name({"name": "小安", "user_id": "u1"}, user_id=None)
        other = await get_identity(user_id="u2")
        assert other["ai_name"] == "Angela"
        assert other["customized"] is False
