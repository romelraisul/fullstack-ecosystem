import logging

logger = logging.getLogger(__name__)

_OTEL_INITIALIZED = False

try:
    from opentelemetry import trace  # type: ignore
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter,  # type: ignore
    )
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore
    from opentelemetry.sdk.trace import TracerProvider  # type: ignore
    from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore
except Exception:  # pragma: no cover
    trace = None


def init_tracing(app, endpoint: str | None = None, service_name: str = "ultimate-summary"):
    global _OTEL_INITIALIZED
    if _OTEL_INITIALIZED:
        return False
    if not trace:
        logger.info("OpenTelemetry not installed; skipping tracing setup")
        return False
    try:
        provider = TracerProvider()
        if endpoint:
            exporter = OTLPSpanExporter(endpoint=endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
        _OTEL_INITIALIZED = True
        logger.info("Tracing initialized (endpoint=%s)", endpoint)
        return True
    except Exception as e:  # pragma: no cover
        logger.warning("Tracing initialization failed: %s", e)
        return False


__all__ = ["init_tracing"]
