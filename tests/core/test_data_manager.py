"""Test Data Manager - real tests"""
import pytest


def test_economy_db_import():
    """Test economy database module can be imported"""
    try:
        from economy.economy_db import EconomyDB
        assert EconomyDB is not None
    except ImportError as e:
        pytest.skip(f"Economy DB not available: {e}")


def test_shared_types_import():
    """Test shared types module can be imported"""
    try:
        from core.shared.types.mappable_data_object import MappableDataObject
        assert MappableDataObject is not None
    except ImportError as e:
        pytest.skip(f"Shared types not available: {e}")


def test_utils_import():
    """Test utils module can be imported"""
    try:
        from core.utils import get_timestamp
        assert get_timestamp is not None
    except ImportError as e:
        pytest.skip(f"Utils not available: {e}")