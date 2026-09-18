"""Tests for llm_routes /llm/config GET+POST (Desktop Settings persistence).

Covers:
- Route registration (GET+POST /llm/config alongside /llm/status + /llm/switch)
- POST validation: empty body, unknown keys, bad enum, out-of-range numbers
- POST valid patch → writes llm.user.yaml via tiered_loader (tmp root)
- GET returns merged subset
- tiered_loader.write_user_config: empty patch / unknown path / merge roundtrip
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps/backend/src"))


@pytest.mark.asyncio
class TestLLMConfigRoutes:
    async def test_router_has_config_paths(self):
        from api.routes.llm_routes import router

        paths = {r.path for r in router.routes}
        assert "/llm/status" in paths
        assert "/llm/switch" in paths
        assert "/llm/config" in paths

    async def test_router_config_methods(self):
        from api.routes.llm_routes import router

        methods = set()
        for r in router.routes:
            if r.path == "/llm/config":
                methods.update(r.methods or set())
        assert "GET" in methods
        assert "POST" in methods

    async def test_post_empty_body_rejected(self):
        from api.routes.llm_routes import llm_config_set

        res = await llm_config_set({})
        assert res["ok"] is False
        assert "non-empty" in res["error"]

    async def test_post_unknown_key_rejected(self):
        from api.routes.llm_routes import llm_config_set

        res = await llm_config_set({"deployment.evil": "x"})
        assert res["ok"] is False
        assert "deployment.evil" in res["error"]
        assert "deployment.mode" in res["error"]  # allowed list shown

    async def test_post_bad_enum_rejected(self):
        from api.routes.llm_routes import llm_config_set

        res = await llm_config_set({"deployment.mode": "mars"})
        assert res["ok"] is False
        assert "local" in res["error"]

    async def test_post_out_of_range_rejected(self):
        from api.routes.llm_routes import llm_config_set

        res = await llm_config_set({"settings.defaults.temperature": 9.9})
        assert res["ok"] is False
        assert "within" in res["error"]
        res = await llm_config_set({"settings.defaults.max_tokens": -5})
        assert res["ok"] is False

    async def test_post_non_bool_rejected(self):
        from api.routes.llm_routes import llm_config_set

        res = await llm_config_set({"web_search.enabled": "yes-please"})
        assert res["ok"] is False
        assert "true/false" in res["error"]

    async def test_post_valid_writes_user_yaml(self, tmp_path, monkeypatch):
        import core.system.config.tiered_loader as tl
        import yaml
        from api.routes.llm_routes import llm_config_set

        sys_dir = tmp_path / "system"
        sys_dir.mkdir()
        monkeypatch.setattr(tl, "_CONFIGS_ROOT", tmp_path)
        monkeypatch.setattr(tl, "_cache", {})

        res = await llm_config_set(
            {
                "deployment.mode": "local+llm",
                "settings.defaults.temperature": 0.8,
                "settings.defaults.max_tokens": 1024,
                "web_search.enabled": True,
                "settings.preferred_backend": "ollama-llama3",
            }
        )
        assert res["ok"] is True
        assert res["restart_required"] is True
        assert "deployment.mode" in res["updated"]

        on_disk = yaml.safe_load((sys_dir / "llm.user.yaml").read_text(encoding="utf-8"))
        assert on_disk["deployment"]["mode"] == "local+llm"
        assert on_disk["settings"]["defaults"]["temperature"] == 0.8
        assert on_disk["settings"]["defaults"]["max_tokens"] == 1024
        assert on_disk["web_search"]["enabled"] is True
        assert on_disk["settings"]["preferred_backend"] == "ollama-llama3"

    async def test_get_returns_subset(self, monkeypatch):
        import core.system.config.tiered_loader as tl
        from api.routes.llm_routes import llm_config_get

        monkeypatch.setattr(
            tl,
            "get_config",
            lambda path: {
                "deployment": {"mode": "auto", "selection": "available"},
                "settings": {"defaults": {"temperature": 0.5, "max_tokens": 256}},
                "unrelated": {"x": 1},
            },
        )
        res = await llm_config_get()
        assert res["ok"] is True
        assert res["config"]["deployment.mode"] == "auto"
        assert res["config"]["settings.defaults.temperature"] == 0.5
        assert "unrelated" not in str(res["config"])


@pytest.mark.asyncio
class TestWriteUserConfig:
    async def test_empty_patch_rejected(self, tmp_path, monkeypatch):
        import core.system.config.tiered_loader as tl

        monkeypatch.setattr(tl, "_CONFIGS_ROOT", tmp_path)
        ok, msg = tl.write_user_config("system/llm", {})
        assert ok is False

    async def test_unknown_path_rejected(self, tmp_path, monkeypatch):
        import core.system.config.tiered_loader as tl

        monkeypatch.setattr(tl, "_CONFIGS_ROOT", tmp_path)
        ok, msg = tl.write_user_config("nope/nothing", {"a": 1})
        assert ok is False

    async def test_merge_roundtrip(self, tmp_path, monkeypatch):
        import core.system.config.tiered_loader as tl
        import yaml

        sys_dir = tmp_path / "system"
        sys_dir.mkdir()
        (sys_dir / "llm.user.yaml").write_text(
            yaml.safe_dump({"deployment": {"mode": "local"}}), encoding="utf-8"
        )
        monkeypatch.setattr(tl, "_CONFIGS_ROOT", tmp_path)
        monkeypatch.setattr(tl, "_cache", {"system/llm": {"stale": True}})

        ok, _ = tl.write_user_config("system/llm", {"settings": {"defaults": {"temperature": 0.3}}})
        assert ok is True
        on_disk = yaml.safe_load((sys_dir / "llm.user.yaml").read_text(encoding="utf-8"))
        assert on_disk["deployment"]["mode"] == "local"  # preserved
        assert on_disk["settings"]["defaults"]["temperature"] == 0.3
        assert "system/llm" not in tl._cache  # invalidated
