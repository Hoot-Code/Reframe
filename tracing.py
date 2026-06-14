"""
tracing.py —
OpenTelemetry distributed tracing for ReFrame bot.
Optional — enabled via FF_TRACING=true environment variable.
"""

import logging
from config import FEATURE_FLAGS, CONFIG

logger = logging.getLogger(__name__)

_tracer = None


def init_tracing(service_name: str = "reframe-bot"):
    global _tracer
    if not FEATURE_FLAGS.get("enable_tracing"):
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(service_name)
        logger.info(f"OpenTelemetry tracing initialized → {service_name}")
    except ImportError:
        logger.warning("opentelemetry packages not installed — tracing disabled")
    except Exception as exc:
        logger.error(f"Tracing init failed: {exc}")


def trace_span(name: str):
    """Context manager for creating a trace span. No-op if tracing disabled."""
    if _tracer is None:
        return _NoopSpan()
    return _tracer.start_as_current_span(name)


class _NoopSpan:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def set_attribute(self, key, value):
        pass
    def add_event(self, name, attributes=None):
        pass
