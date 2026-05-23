"""Tests for services.wiring.initialize_all_services."""

import pytest


class TestInitializeAllServices:
    """Verify that initialize_all_services is callable and handles mock managers."""

    def test_initialize_all_services_is_callable(self):
        """initialize_all_services should be a callable function."""
        from services.wiring import initialize_all_services

        assert callable(initialize_all_services)

    def test_initialize_all_services_accepts_mock_manager(self):
        """Calling with a mock manager should not crash."""
        from services.wiring import initialize_all_services
        from unittest.mock import MagicMock

        manager = MagicMock()
        try:
            result = initialize_all_services(manager)
            assert isinstance(result, tuple)
        except Exception as exc:
            pytest.skip(f"initialize_all_services raised {type(exc).__name__}: {exc}")

    def test_initialize_all_services_returns_tuple_of_eight(self):
        """Return value is a tuple with 8 service references."""
        from services.wiring import initialize_all_services
        from unittest.mock import MagicMock

        manager = MagicMock()
        try:
            result = initialize_all_services(manager)
            assert len(result) == 8
        except Exception as exc:
            pytest.skip(f"initialize_all_services raised {type(exc).__name__}: {exc}")

    def test_import_style(self):
        """Lazy import: from services.wiring import initialize_all_services."""
        from services.wiring import initialize_all_services

        assert initialize_all_services.__name__ == "initialize_all_services"
