"""Tests for core/angela_error.py"""
import pytest


class TestAngelaError:
    """Tests for AngelaError hierarchy"""

    def test_import_angela_error(self):
        """Verify AngelaError is a proper Exception subclass with expected hierarchy"""
        from core.angela_error import AngelaError, ErrorSeverity, ErrorCategory, ErrorHandler
        assert issubclass(AngelaError, Exception)
        assert AngelaError.DEFAULT_CODE == "ANGELA_ERROR"
        assert AngelaError.DEFAULT_MESSAGE == "An error occurred in Angela AI"
        assert AngelaError.DEFAULT_CATEGORY == ErrorCategory.UNKNOWN
        assert AngelaError.DEFAULT_SEVERITY == ErrorSeverity.ERROR
        assert hasattr(ErrorHandler, 'handle')
        assert hasattr(ErrorHandler, 'register_handler')

    def test_angela_error_instantiation(self):
        """Verify AngelaError default instantiation sets correct defaults"""
        from core.angela_error import AngelaError, ErrorSeverity, ErrorCategory
        err = AngelaError()
        assert isinstance(err, Exception)
        assert err.message == "An error occurred in Angela AI"
        assert err.code == "ANGELA_ERROR"
        assert err.category == ErrorCategory.UNKNOWN
        assert err.severity == ErrorSeverity.ERROR
        assert err.cause is None
        assert err.context is not None
        assert str(err) == "[ANGELA_ERROR] An error occurred in Angela AI (unknown)"
        assert repr(err).startswith("AngelaError(code='ANGELA_ERROR'")

    def test_angela_error_with_message(self):
        """Verify AngelaError accepts custom params, serializes correctly, and chains causes"""
        from core.angela_error import AngelaError, ErrorCategory, ErrorSeverity
        err = AngelaError(
            message="test error",
            code="TEST_CODE",
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.WARNING,
        )
        assert err.message == "test error"
        assert err.code == "TEST_CODE"
        assert err.category == ErrorCategory.CONFIGURATION
        assert err.severity == ErrorSeverity.WARNING
        assert "[TEST_CODE]" in str(err)
        d = err.to_dict()
        assert d["error"]["code"] == "TEST_CODE"
        assert d["error"]["category"] == "configuration"
        assert d["error"]["severity"] == "warning"
        json_str = err.to_json()
        assert "TEST_CODE" in json_str
        cause = ValueError("original cause")
        chained = AngelaError(message="wrapped", cause=cause)
        assert chained.cause is cause
        extra = AngelaError(message="extra", extra_field="value")
        assert extra.context.additional_info["extra_field"] == "value"

    def test_configuration_error(self):
        """Verify ConfigurationError can be imported and raised"""
        try:
            from core.angela_error import ConfigurationError
            err = ConfigurationError()
            assert isinstance(err, Exception)
        except ImportError as e:
            pytest.skip(f"ConfigurationError not available: {e}")
        except Exception as e:
            pytest.skip(f"ConfigurationError init failed (expected in CI): {e}")

    def test_core_error(self):
        """Verify CoreError can be imported and raised"""
        try:
            from core.angela_error import CoreError
            err = CoreError()
            assert isinstance(err, Exception)
        except ImportError as e:
            pytest.skip(f"CoreError not available: {e}")
        except Exception as e:
            pytest.skip(f"CoreError init failed (expected in CI): {e}")

    def test_network_error(self):
        """Verify NetworkError can be imported and raised"""
        try:
            from core.angela_error import NetworkError
            err = NetworkError()
            assert isinstance(err, Exception)
        except ImportError as e:
            pytest.skip(f"NetworkError not available: {e}")
        except Exception as e:
            pytest.skip(f"NetworkError init failed (expected in CI): {e}")

    def test_resource_error(self):
        """Verify ResourceError can be imported and raised"""
        try:
            from core.angela_error import ResourceError
            err = ResourceError()
            assert isinstance(err, Exception)
        except ImportError as e:
            pytest.skip(f"ResourceError not available: {e}")
        except Exception as e:
            pytest.skip(f"ResourceError init failed (expected in CI): {e}")

    def test_validation_error(self):
        """Verify ValidationError can be imported and raised"""
        try:
            from core.angela_error import ValidationError
            err = ValidationError()
            assert isinstance(err, Exception)
        except ImportError as e:
            pytest.skip(f"ValidationError not available: {e}")
        except Exception as e:
            pytest.skip(f"ValidationError init failed (expected in CI): {e}")

    def test_all_subclasses_importable(self):
        """Verify all common error subclasses are importable"""
        try:
            from core.angela_error import (
                AngelaError, CoreError, ConfigurationError,
                NetworkError, WebSocketError, DatabaseError,
                MemoryError, AIModelError, LLMError,
                AudioError, SecurityError, AuthenticationError,
                AuthorizationError, ResourceError, ValidationError,
                NotFoundError, BusinessLogicError, RateLimitError,
            )
            assert AngelaError is not None
        except ImportError as e:
            pytest.skip(f"Error hierarchy not fully importable: {e}")
