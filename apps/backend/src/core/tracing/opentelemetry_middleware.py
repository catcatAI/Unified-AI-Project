"""
Angela AI - OpenTelemetry Tracing Middleware
Provides distributed tracing for FastAPI
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    OPEN TELEMETRY_AVAILABLE = True
except ImportError:
    OPEN TELEMETRY_AVAILABLE = False
    logger.warning("OpenTelemetry not available. Tracing disabled.")


def init_tracing(
    service_name: str = "angela-backend",
    endpoint: Optional[str] = None,
) -> None:
    """Initialize OpenTelemetry tracing."""
    if not OPEN TELEMETRY_AVAILABLE:
        logger.info("OpenTelemetry not installed. Skipping tracing setup.")
        return

    # Create resource
    resource = Resource.create({"service.name": service_name})

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add console exporter for debugging
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)

    # Set as global provider
    trace.set_tracer_provider(provider)

    logger.info("OpenTelemetry tracing initialized for service: %s", service_name)


def instrument_app(app) -> None:
    """Instrument a FastAPI app with OpenTelemetry."""
    if not OPEN TELEMETRY_AVAILABLE:
        return

    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented with OpenTelemetry")
    except Exception as e:
        logger.warning("Failed to instrument FastAPI: %s", e)


def get_tracer(name: str = "angela"):
    """Get a tracer instance."""
    if not OPEN TELEMETRY_AVAILABLE:
        return None
    return trace.get_tracer(name)
