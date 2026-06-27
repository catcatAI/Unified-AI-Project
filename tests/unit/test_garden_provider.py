"""Tests for services.llm.providers.garden"""
from unittest.mock import MagicMock, patch

import pytest


class TestGARDENBackend:
    def test_import(self):
        from services.llm.providers.garden import GARDENBackend

        assert GARDENBackend is not None

    def test_instantiation_defaults(self):
        from services.llm.providers.garden import GARDENBackend

        instance = GARDENBackend()
        assert instance.model == "garden-1g"
        assert instance.timeout == 30.0
        assert instance.checkpoint == ""

    def test_instantiation_custom(self):
        from services.llm.providers.garden import GARDENBackend

        instance = GARDENBackend(model="garden-2g", checkpoint="/tmp/ckpt", timeout=60.0)
        assert instance.model == "garden-2g"
        assert instance.checkpoint == "/tmp/ckpt"
        assert instance.timeout == 60.0

    async def test_generate(self):
        from services.llm.providers.garden import GARDENBackend

        mock_engine = MagicMock()
        mock_engine.process.return_value = "garden response"
        instance = GARDENBackend()
        instance._engine = mock_engine
        result = await instance.generate("hello")
        assert result.text == "garden response"
        assert result.backend == "garden"
        assert result.model == "garden-1g"
        mock_engine.process.assert_called_once()

    async def test_generate_fallback_on_empty(self):
        from services.llm.providers.garden import GARDENBackend

        mock_engine = MagicMock()
        mock_engine.process.return_value = ""
        instance = GARDENBackend()
        instance._engine = mock_engine
        result = await instance.generate("hello")
        assert result.text == "抱歉，我暂时无法理解你的意思。"

    async def test_generate_with_context(self):
        from services.llm.providers.garden import GARDENBackend

        mock_engine = MagicMock()
        mock_engine.process.return_value = "contextual response"
        instance = GARDENBackend()
        instance._engine = mock_engine
        result = await instance.generate("test", context={"key": "val"})
        assert result.text == "contextual response"
        mock_engine.process.assert_called_with("test", context={"key": "val"})

    async def test_generate_error_returns_error_response(self):
        from services.llm.providers.garden import GARDENBackend

        mock_engine = MagicMock()
        mock_engine.process.side_effect = RuntimeError("garden error")
        instance = GARDENBackend()
        instance._engine = mock_engine
        result = await instance.generate("hello")
        assert result.text == ""
        assert "garden error" in result.error

    async def test_check_health(self):
        from services.llm.providers.garden import GARDENBackend

        instance = GARDENBackend()
        instance._engine = MagicMock()
        healthy = await instance.check_health()
        assert healthy is True

    async def test_check_health_no_engine_triggers_get_engine(self):
        from services.llm.providers.garden import GARDENBackend

        instance = GARDENBackend()
        with patch("ai.garden.garden_engine.GARDENEngine") as MockEngine:
            MockEngine.return_value = MagicMock()
            healthy = await instance.check_health()
            assert healthy is True
