"""core.tracing.opentelemetry_middleware OpenTelemetry 追蹤測試"""

from apps.backend.src.core.tracing.opentelemetry_middleware import (
    OPENTELEMETRY_AVAILABLE,
    get_tracer,
    init_tracing,
    instrument_app,
)


class TestOpenTelemetryMiddleware:
    def test_init_tracing_no_crash(self):
        assert init_tracing(service_name="test-service") is None

    def test_instrument_app_no_crash(self):
        class FakeApp:
            pass

        assert instrument_app(FakeApp()) is None

    def test_get_tracer_returns_none_if_unavailable(self):
        tracer = get_tracer("test")
        if OPENTELEMETRY_AVAILABLE:
            assert tracer is not None
        else:
            assert tracer is None

    def test_available_flag_is_bool(self):
        assert isinstance(OPENTELEMETRY_AVAILABLE, bool)
