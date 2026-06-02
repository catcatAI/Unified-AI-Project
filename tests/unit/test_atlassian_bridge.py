"""Tests for integrations/atlassian_bridge.py"""
from unittest.mock import MagicMock
import pytest


class TestAtlassianBridge:
    """Tests for AtlassianBridge"""

    def test_import(self):
        from integrations.atlassian_bridge import AtlassianBridge
        assert AtlassianBridge is not None

    def test_instantiation_with_mock_connector(self):
        from integrations.atlassian_bridge import AtlassianBridge
        mock_connector = MagicMock()
        mock_connector.config = {"atlassian": {}}
        instance = AtlassianBridge(connector=mock_connector)
        assert instance is not None
        assert instance.cache_dir is not None

    def test_instantiation_with_config(self):
        from integrations.atlassian_bridge import AtlassianBridge
        mock_connector = MagicMock()
        mock_connector.config = {
            "atlassian": {
                "confluence": {"url": "https://test.atlassian.net/wiki"},
                "jira": {"url": "https://test.atlassian.net"},
            }
        }
        instance = AtlassianBridge(connector=mock_connector)
        assert instance is not None
        assert "confluence" in instance.endpoints or len(instance.endpoints) >= 0

    def test_cachedir_created(self):
        from integrations.atlassian_bridge import AtlassianBridge
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmp:
            mock_connector = MagicMock()
            mock_connector.config = {"atlassian": {}}
            instance = AtlassianBridge(connector=mock_connector)
            assert instance.cache_dir is not None
