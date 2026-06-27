"""Tests for services.llm.providers.ed3n"""
from unittest.mock import MagicMock, patch

import pytest


class TestED3NBackend:
    def test_import(self):
        from services.llm.providers.ed3n import ED3NBackend

        assert ED3NBackend is not None

    def test_instantiation_defaults(self):
        from services.llm.providers.ed3n import ED3NBackend

        instance = ED3NBackend()
        assert instance.model == "ed3n-v1"
        assert instance.timeout == 30.0
        assert instance.depth == "auto"

    def test_instantiation_custom(self):
        from services.llm.providers.ed3n import ED3NBackend

        instance = ED3NBackend(
            base_url="http://test", model="ed3n-v2",
            api_key="key123", timeout=60.0, depth="deep",
        )
        assert instance.model == "ed3n-v2"
        assert instance.api_key == "key123"
        assert instance.depth == "deep"

    async def test_generate_reflex(self):
        from services.llm.providers.ed3n import ED3NBackend

        mock_engine = MagicMock()
        mock_engine.process_reflex.return_value = "reflex response"
        instance = ED3NBackend()
        instance._engine = mock_engine
        result = await instance.generate("hello", depth="reflex")
        assert result.text == "reflex response"
        assert result.backend == "ed3n"
        mock_engine.process_reflex.assert_called_once_with("hello")

    async def test_generate_deep(self):
        from services.llm.providers.ed3n import ED3NBackend

        mock_engine = MagicMock()
        mock_engine.process.return_value = "deep response"
        instance = ED3NBackend()
        instance._engine = mock_engine
        result = await instance.generate("hello", depth="deep")
        assert result.text == "deep response"
        mock_engine.process.assert_called_once()

    async def test_generate_falls_back_to_shallow(self):
        from services.llm.providers.ed3n import ED3NBackend

        mock_engine = MagicMock()
        mock_engine.process.return_value = ""
        mock_engine.process_shallow.return_value = "shallow fallback"
        instance = ED3NBackend()
        instance._engine = mock_engine
        result = await instance.generate("hello", depth="deep")
        assert result.text == "shallow fallback"
        mock_engine.process_shallow.assert_called_once()

    async def test_generate_with_context(self):
        from services.llm.providers.ed3n import ED3NBackend

        mock_engine = MagicMock()
        mock_engine.process.return_value = "context aware"
        instance = ED3NBackend()
        instance._engine = mock_engine
        result = await instance.generate("test", context={"key": "val"})
        assert result.text == "context aware"

    async def test_generate_error_returns_error_response(self):
        from services.llm.providers.ed3n import ED3NBackend

        mock_engine = MagicMock()
        mock_engine.process.side_effect = RuntimeError("engine error")
        instance = ED3NBackend()
        instance._engine = mock_engine
        result = await instance.generate("hello", depth="deep")
        assert result.text == ""
        assert "engine error" in result.error

    async def test_check_health(self):
        from services.llm.providers.ed3n import ED3NBackend

        instance = ED3NBackend()
        instance._engine = MagicMock()
        healthy = await instance.check_health()
        assert healthy is True

    async def test_check_health_no_engine(self):
        from services.llm.providers.ed3n import ED3NBackend

        instance = ED3NBackend()
        with patch("ai.ed3n.ed3n_engine.ED3NEngine") as MockEngine:
            MockEngine.return_value = MagicMock()
            healthy = await instance.check_health()
            assert healthy is True
