"""Tests for Angela AI Unified Error Handling System."""

import json
import pytest
from apps.backend.src.core.angela_error import (
    AngelaError, ErrorSeverity, ErrorCategory, ErrorContext,
    CoreError, ConfigurationError, NetworkError, WebSocketError,
    DatabaseError, MemoryError, AIModelError, LLMError,
    AudioError, SecurityError, ValidationError, NotFoundError,
    ErrorHandler, get_error_handler, safe_execute,
)


class TestErrorContext:
    def test_default_creation(self):
        ctx = ErrorContext()
        assert ctx.module == ""
        assert ctx.function == ""
        assert ctx.line == 0

    def test_to_dict(self):
        ctx = ErrorContext(module="test_mod", function="test_func", line=42)
        d = ctx.to_dict()
        assert d["module"] == "test_mod"
        assert d["function"] == "test_func"
        assert d["line"] == 42
        assert "timestamp" in d

    def test_to_dict_with_additional_info(self):
        ctx = ErrorContext(additional_info={"key": "val"})
        d = ctx.to_dict()
        assert d["additional_info"]["key"] == "val"


class TestAngelaErrorBase:
    def test_default_creation(self):
        err = AngelaError()
        assert err.message == AngelaError.DEFAULT_MESSAGE
        assert err.code == AngelaError.DEFAULT_CODE
        assert err.category == ErrorCategory.UNKNOWN
        assert err.severity == ErrorSeverity.ERROR

    def test_custom_message(self):
        err = AngelaError("custom message")
        assert err.message == "custom message"

    def test_custom_code_and_category(self):
        err = AngelaError("msg", code="MY_CODE", category=ErrorCategory.NETWORK)
        assert err.code == "MY_CODE"
        assert err.category == ErrorCategory.NETWORK

    def test_to_dict_structure(self):
        err = AngelaError("test error", code="TEST")
        d = err.to_dict()
        assert d["error"]["code"] == "TEST"
        assert d["error"]["message"] == "test error"
        assert d["error"]["category"] == "unknown"
        assert d["error"]["severity"] == "error"
        assert "context" in d["error"]

    def test_to_json(self):
        err = AngelaError("json test")
        json_str = err.to_json()
        parsed = json.loads(json_str)
        assert parsed["error"]["message"] == "json test"

    def test_str_repr(self):
        err = AngelaError("display test", code="DISP")
        assert "DISP" in str(err)
        assert "display test" in str(err)
        assert "AngelaError" in repr(err)


class TestErrorHierarchy:
    def test_core_error_defaults(self):
        err = CoreError()
        assert err.code == "CORE_ERROR"
        assert err.category == ErrorCategory.CORE

    def test_configuration_error(self):
        err = ConfigurationError("bad config")
        assert err.code == "CONFIG_ERROR"
        assert err.category == ErrorCategory.CONFIGURATION

    def test_network_error(self):
        err = NetworkError("timeout")
        assert err.code == "NETWORK_ERROR"
        assert err.category == ErrorCategory.NETWORK

    def test_websocket_error(self):
        err = WebSocketError("disconnected")
        assert err.code == "WEBSOCKET_ERROR"
        assert err.category == ErrorCategory.WEBSOCKET

    def test_database_error(self):
        err = DatabaseError("connection failed")
        assert err.code == "DATABASE_ERROR"
        assert err.category == ErrorCategory.DATABASE

    def test_memory_error(self):
        err = MemoryError("allocation failed")
        assert err.code == "MEMORY_ERROR"
        assert err.category == ErrorCategory.MEMORY

    def test_ai_model_error(self):
        err = AIModelError("inference failed")
        assert err.code == "AI_MODEL_ERROR"
        assert err.category == ErrorCategory.AI_MODEL

    def test_llm_error(self):
        err = LLMError("token limit")
        assert err.code == "LLM_ERROR"
        assert err.category == ErrorCategory.LLM

    def test_security_error(self):
        err = SecurityError("unauthorized")
        assert err.code == "SECURITY_ERROR"
        assert err.category == ErrorCategory.SECURITY
        assert err.severity == ErrorSeverity.CRITICAL

    def test_validation_error(self):
        err = ValidationError("invalid input")
        assert err.code == "VALIDATION_ERROR"
        assert err.category == ErrorCategory.VALIDATION

    def test_not_found_error(self):
        err = NotFoundError("resource missing")
        assert err.code == "NOT_FOUND_ERROR"
        assert err.category == ErrorCategory.BUSINESS_LOGIC

    def test_is_angela_error_instance(self):
        for exc in [CoreError(), NetworkError(), ValidationError(), AudioError()]:
            assert isinstance(exc, AngelaError)

    def test_chained_cause(self):
        cause = ValueError("original problem")
        err = AngelaError("wrapped", cause=cause)
        assert err.cause is cause

    def test_error_with_extra_kwargs(self):
        err = AngelaError("extra", extra_field="value", user="test")
        assert err.context.additional_info["extra_field"] == "value"
        assert err.context.additional_info["user"] == "test"


class TestErrorHandler:
    def test_get_error_handler_singleton(self):
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        assert handler1 is handler2

    def test_handler_handles_error(self):
        handler = get_error_handler()
        err = AngelaError("handled error")
        handler.register_handler(AngelaError, lambda e: "handled")
        result = handler.handle(err)
        assert result == "handled"
        assert result is not None

    def test_safe_execute_success(self):
        result = safe_execute(lambda: 42)
        assert result == 42

    def test_safe_execute_failure(self):
        def failing():
            raise ValueError("fail")
        result = safe_execute(failing)
        assert result is None

    def test_safe_execute_custom_default(self):
        def failing():
            raise ValueError("fail")
        result = safe_execute(failing, default_return="fallback")
        assert result == "fallback"
