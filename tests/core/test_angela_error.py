"""Tests for Angela AI Unified Error Handling System."""

import json

import pytest

try:
    from apps.backend.src.core.angela_error import (
        AIModelError,
        AngelaError,
        AudioError,
        BusinessLogicError,
        CardError,
        ConfigurationError,
        CoreError,
        DatabaseError,
        ErrorCategory,
        ErrorContext,
        ErrorHandler,
        ErrorSeverity,
        IntentError,
        LLMError,
        MemoryError,
        MonitoringError,
        NetworkError,
        NotFoundError,
        RateLimitError,
        ResourceError,
        ResourceNotFoundError,
        SecurityError,
        ServiceError,
        ValidationError,
        WebSocketError,
    )
except ImportError:
    pytest.skip("AngelaError module not available", allow_module_level=True)


class TestErrorContext:
    def test_default_creation(self):
        ctx = ErrorContext()
        assert ctx.additional_info == {}

    def test_with_kwargs(self):
        ctx = ErrorContext(module="test_mod", function="test_func", line=42)
        assert ctx.additional_info["module"] == "test_mod"
        assert ctx.additional_info["function"] == "test_func"
        assert ctx.additional_info["line"] == 42

    def test_repr(self):
        ctx = ErrorContext(key="val")
        assert "key" in repr(ctx)


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
        assert err.code == "CORE_ERR"
        assert err.category == ErrorCategory.CORE

    def test_configuration_error(self):
        err = ConfigurationError("bad config")
        assert err.code == "CONFIG_ERR"
        assert err.category == ErrorCategory.CONFIGURATION

    def test_network_error(self):
        err = NetworkError("timeout")
        assert err.code == "NET_ERR"
        assert err.category == ErrorCategory.NETWORK

    def test_websocket_error(self):
        err = WebSocketError("disconnected")
        assert err.code == "WS_ERR"
        assert err.category == ErrorCategory.WEBSOCKET

    def test_database_error(self):
        err = DatabaseError("connection failed")
        assert err.code == "DB_ERR"
        assert err.category == ErrorCategory.DATABASE

    def test_memory_error(self):
        err = MemoryError("allocation failed")
        assert err.code == "MEM_ERR"
        assert err.category == ErrorCategory.MEMORY

    def test_ai_model_error(self):
        err = AIModelError("inference failed")
        assert err.code == "AI_ERR"
        assert err.category == ErrorCategory.AI_MODEL

    def test_llm_error(self):
        err = LLMError("token limit")
        assert err.code == "LLM_ERR"
        assert err.category == ErrorCategory.LLM

    def test_security_error(self):
        err = SecurityError("unauthorized")
        assert err.code == "SEC_ERR"
        assert err.category == ErrorCategory.SECURITY

    def test_validation_error(self):
        err = ValidationError("invalid input")
        assert err.code == "VAL_ERR"
        assert err.category == ErrorCategory.VALIDATION

    def test_not_found_error(self):
        err = NotFoundError("resource missing")
        assert err.code == "NOT_FOUND"
        assert err.category == ErrorCategory.NOT_FOUND

    def test_audio_error(self):
        err = AudioError("audio processing failed")
        assert err.code == "AUDIO_ERR"
        assert err.category == ErrorCategory.AUDIO

    def test_resource_error(self):
        err = ResourceError("resource exhausted")
        assert err.code == "RES_ERR"
        assert err.category == ErrorCategory.RESOURCE

    def test_resource_not_found_error(self):
        err = ResourceNotFoundError("resource missing", resource="test_file")
        assert err.code == "NOT_FOUND_ERR"
        assert err.category == ErrorCategory.NOT_FOUND

    def test_business_logic_error(self):
        err = BusinessLogicError("business rule violated")
        assert err.code == "BIZ_ERR"
        assert err.category == ErrorCategory.BUSINESS_LOGIC

    def test_rate_limit_error(self):
        err = RateLimitError("too many requests")
        assert err.code == "RATE_LIMIT"
        assert err.category == ErrorCategory.RATE_LIMIT

    def test_intent_error(self):
        err = IntentError("intent detection failed")
        assert err.code == "INTENT_ERR"
        assert err.category == ErrorCategory.INTENT

    def test_card_error(self):
        err = CardError("card pipeline failed")
        assert err.code == "CARD_ERR"
        assert err.category == ErrorCategory.CARD

    def test_service_error(self):
        err = ServiceError("service unavailable")
        assert err.code == "SVC_ERR"
        assert err.category == ErrorCategory.SERVICE

    def test_monitoring_error(self):
        err = MonitoringError("monitoring failure")
        assert err.code == "MON_ERR"
        assert err.category == ErrorCategory.MONITORING

    def test_is_angela_error_instance(self):
        for exc in [CoreError(), NetworkError(), ValidationError(), AudioError()]:
            assert isinstance(exc, AngelaError)

    def test_chained_cause(self):
        cause = ValueError("original problem")
        err = AngelaError("wrapped", cause=cause)
        assert err.cause is cause

    def test_error_extra_kwargs_stored_in_context(self):
        err = AngelaError("extra", extra_field="value", user="test")
        assert err.context.additional_info["extra_field"] == "value"
        assert err.context.additional_info["user"] == "test"


class TestErrorHandler:
    def test_handler_register_and_handle(self):
        handler = ErrorHandler()
        results = []
        handler.register_handler("AngelaError", lambda e: results.append(e))
        err = AngelaError("test error")
        handler.handle(err)
        assert len(results) == 1
        assert results[0] is err

    def test_handler_returns_list_of_results(self):
        handler = ErrorHandler()
        handler.register_handler("AngelaError", lambda e: "result1")
        handler.register_handler("AngelaError", lambda e: "result2")
        err = AngelaError("test error")
        result = handler.handle(err)
        assert result == ["result1", "result2"]

    def test_handler_unregistered_error_type(self):
        handler = ErrorHandler()
        result = handler.handle(ValueError("unknown"))
        assert result == []
