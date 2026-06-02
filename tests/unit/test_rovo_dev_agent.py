"""Tests for integrations/rovo_dev_agent.py"""
import pytest


class TestRovoDevAgent:
    """Tests for RovoDevAgent"""

    def test_import(self):
        from integrations.rovo_dev_agent import RovoDevAgent
        assert RovoDevAgent is not None

    def test_instantiation(self):
        from integrations.rovo_dev_agent import RovoDevAgent
        instance = RovoDevAgent(config={})
        assert instance is not None
        assert instance.is_active is False
        assert instance.config == {}

    def test_instantiation_with_manager(self):
        from integrations.rovo_dev_agent import RovoDevAgent
        mock_mgr = object()
        instance = RovoDevAgent(config={"key": "val"}, agent_manager=mock_mgr)
        assert instance.agent_manager is mock_mgr
        assert instance.config["key"] == "val"

    @pytest.mark.asyncio
    async def test_start(self):
        from integrations.rovo_dev_agent import RovoDevAgent
        instance = RovoDevAgent(config={})
        assert instance.is_active is False
        await instance.start()
        assert instance.is_active is True

    @pytest.mark.asyncio
    async def test_stop(self):
        from integrations.rovo_dev_agent import RovoDevAgent
        instance = RovoDevAgent(config={})
        await instance.start()
        await instance.stop()
        assert instance.is_active is False

    @pytest.mark.asyncio
    async def test_process_task_not_active(self):
        from integrations.rovo_dev_agent import RovoDevAgent
        instance = RovoDevAgent(config={})
        with pytest.raises(Exception):
            await instance.process_task({"name": "test"})

    @pytest.mark.asyncio
    async def test_process_task_active(self):
        from integrations.rovo_dev_agent import RovoDevAgent
        instance = RovoDevAgent(config={})
        await instance.start()
        result = await instance.process_task({"name": "test"})
        assert result["status"] == "completed"
