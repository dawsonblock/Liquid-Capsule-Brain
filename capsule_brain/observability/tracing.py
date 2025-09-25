"""OpenTelemetry tracing configuration for Capsule Brain."""

import os
from typing import Any

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

from fastapi import FastAPI

# Global tracer (only if OpenTelemetry is available)
if OPENTELEMETRY_AVAILABLE:
    tracer = trace.get_tracer(__name__)
else:
    tracer = None


def setup_tracing(app: FastAPI) -> None:
    """Setup OpenTelemetry tracing for the application."""
    
    if not OPENTELEMETRY_AVAILABLE:
        return
    
    # Only enable tracing if configured
    if not os.getenv("OTEL_ENABLED", "false").lower() == "true":
        return
    
    # Create resource
    resource = Resource.create({
        "service.name": "capsule-brain",
        "service.version": "1.0.1",
        "deployment.environment": os.getenv("APP_ENV", "development"),
    })
    
    # Set up tracer provider
    trace.set_tracer_provider(TracerProvider(resource=resource))
    
    # Configure OTLP exporter
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument HTTPX client
    HTTPXClientInstrumentor().instrument()


def get_tracer(name: str) -> Any:
    """Get a tracer instance."""
    if OPENTELEMETRY_AVAILABLE:
        return trace.get_tracer(name)
    return None


def create_span(name: str, **attributes):
    """Create a span with the given name and attributes."""
    if tracer:
        return tracer.start_span(name, attributes=attributes)
    return None
