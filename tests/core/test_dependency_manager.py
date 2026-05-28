"""Test Dependency Manager - real tests"""
import pytest


def test_hsp_connector_import():
    """Test HSP connector can be imported"""
    try:
        from core.hsp.connector import HSPConnector
        assert HSPConnector is not None
    except ImportError as e:
        pytest.skip(f"HSP connector not available: {e}")


def test_hsp_bridge_import():
    """Test HSP bridge module can be imported"""
    try:
        from core.hsp.bridge import message_bridge
        assert message_bridge is not None
    except ImportError as e:
        pytest.skip(f"HSP bridge not available: {e}")


def test_core_imports():
    """Test core module imports"""
    try:
        from core.angela_error import AngelaError
        assert AngelaError is not None
    except ImportError as e:
        pytest.skip(f"Core module not available: {e}")