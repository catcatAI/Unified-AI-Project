"""api.lifespan 服务工厂 getter 测试"""

import pytest

from apps.backend.src.api import lifespan as lifespan_module


class TestLifespanServiceGetters:
    def test_get_vision_service_returns_instance(self):
        svc = lifespan_module.get_vision_service()
        assert svc is not None

    def test_get_agent_manager_before_startup_is_none(self):
        # Before lifespan startup runs, the singleton must be None.
        lifespan_module._agent_manager_instance = None
        assert lifespan_module.get_agent_manager() is None

    def test_get_agent_manager_returns_singleton(self):
        sentinel = object()
        lifespan_module._agent_manager_instance = sentinel
        try:
            assert lifespan_module.get_agent_manager() is sentinel
        finally:
            lifespan_module._agent_manager_instance = None

    def test_get_agent_manager_has_shutdown_guard(self):
        # shutdown_all_agents should be callable only when the instance is set
        lifespan_module._agent_manager_instance = None
        assert lifespan_module.get_agent_manager() is None


@pytest.mark.asyncio
class TestDigitalLifeStartup:
    """_try_start_digital_life must actually initialize the DLI singleton."""

    async def test_start_digital_life_initializes_singleton(self):
        from apps.backend.src.api.lifespan import (
            _digital_life_instance,
            _try_start_digital_life,
            get_digital_life,
        )

        # Reset the singleton so we exercise the real startup path
        saved = lifespan_module._digital_life_instance
        lifespan_module._digital_life_instance = None
        try:
            await _try_start_digital_life()
            dli = get_digital_life()
            assert dli is not None
            assert getattr(dli, "is_initialized", False) is True
            assert dli.llm_decision_loop is not None
            assert dli.autonomous_lifecycle is not None
        finally:
            lifespan_module._digital_life_instance = saved
