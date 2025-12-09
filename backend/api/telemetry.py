"""
Lightweight telemetry helpers with optional OTLP / Phoenix integration.
Falls back to logging when tracing backends are unavailable.
"""

import logging
import time
from contextlib import contextmanager
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:  # optional OpenTelemetry
    from opentelemetry import trace  # type: ignore
except Exception:
    trace = None  # type: ignore


@contextmanager
def span(name: str, attributes: Optional[Dict[str, Any]] = None):
    start = time.perf_counter()
    otel_span = None
    if trace:
        tracer = trace.get_tracer(__name__)
        otel_span = tracer.start_span(name)
        if attributes:
            for k, v in attributes.items():
                try:
                    otel_span.set_attribute(k, v)
                except Exception:
                    pass
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        if otel_span:
            try:
                otel_span.set_attribute("duration_ms", duration_ms)
                otel_span.end()
            except Exception:
                pass
        logger.info("span name=%s attrs=%s duration_ms=%.2f", name, attributes or {}, duration_ms)
