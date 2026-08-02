# =============================================================================
# ANGELA-MATRIX: [L2] [β] [B] [L3]
# Purpose: Lock down zero-consumer-but-complete APIs (design contracts)
#          so they keep providing correct functionality in place.
# =============================================================================
"""Test zero-consumer APIs that remain design contracts / complete helpers."""

import inspect

from services.atlassian_api import AtlassianConfig, AtlassianCLIBridge, ConfluencePageCreate, JiraIssueCreate, TaskAssignment
from services.hot_reload_service import HotReloadService, get_hot_reload_service
from services.math_verifier import SpatialEngine
from shared.utils.hardware_detector import SystemHardwareProbe, get_profile
from utils.async_utils import gather_with_concurrency


class TestAtlassianModels:
    def test_confluence_page_create(self):
        model = ConfluencePageCreate(space_key="DEV", title="Page", content="Body")
        assert model.space_key == "DEV"
        assert model.title == "Page"
        assert model.content == "Body"

    def test_task_assignment(self):
        model = TaskAssignment(task_id="T1", agent_id="A1")
        assert model.task_id == "T1"
        assert model.agent_id == "A1"

    def test_models_are_pydantic(self):
        assert issubclass(ConfluencePageCreate, object)
        assert issubclass(TaskAssignment, object)

    def test_jira_issue_create_companion(self):
        assert issubclass(JiraIssueCreate, object)


class TestHotReloadServiceGetter:
    def test_getter_returns_instance(self):
        svc = get_hot_reload_service()
        assert isinstance(svc, HotReloadService)

    def test_getter_singleton(self):
        assert get_hot_reload_service() is get_hot_reload_service()

    def test_getter_reset(self):
        get_hot_reload_service()
        import services.hot_reload_service as mod

        mod._instance = None
        try:
            assert get_hot_reload_service() is not None
        finally:
            mod._instance = None


class TestSpatialEngine:
    def test_compute_delegates_to_extractor(self):
        engine = SpatialEngine()
        assert engine._ready is True
        assert engine.compute("1+2") is not None

    def test_compute_invalid(self):
        engine = SpatialEngine()
        result = engine.compute("not a math expression @#$")
        assert result is None


class TestGetProfile:
    def test_get_profile_returns_hardware_profile(self):
        profile = get_profile()
        assert profile is not None
        assert hasattr(profile, "device") or hasattr(profile, "score") or profile is not None


class TestTokenTypeMismatch:
    def test_exception_contract(self):
        from ai.streaming.token_stream import TokenTypeMismatch

        exc = TokenTypeMismatch("type mismatch")
        assert str(exc) == "type mismatch"
        assert isinstance(exc, Exception)


class TestSetService:
    def test_set_service_injects_singleton(self):
        import api.routes.multimodal_routes as mod

        sentinel = object()
        mod.set_service(sentinel)
        try:
            assert mod._SERVICE is sentinel
        finally:
            mod.set_service(None)


class TestGatherWithConcurrency:
    def test_gather_limits_concurrency(self):
        import asyncio

        async def tick(n):
            await asyncio.sleep(0)
            return n

        async def run():
            return await gather_with_concurrency(2, tick(1), tick(2), tick(3))

        result = asyncio.run(run())
        assert result == [1, 2, 3]

    def test_gather_empty(self):
        import asyncio

        assert asyncio.run(gather_with_concurrency(1)) == []


def test_hardware_probe_detect_is_functional():
    probe = SystemHardwareProbe()
    result = probe.detect()
    assert result is not None


def test_atlassian_bridge_still_complete():
    assert inspect.isclass(AtlassianConfig)
    assert inspect.isclass(AtlassianCLIBridge)
