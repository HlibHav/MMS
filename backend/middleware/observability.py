"""
Observability Middleware

Phoenix tracing and structured logging for engines and tools.
"""

import logging
import functools
import inspect
import time
from typing import Callable, Any, Optional
from contextlib import contextmanager
from inspect import iscoroutinefunction

logger = logging.getLogger(__name__)

# Try to import Phoenix
try:
    from phoenix.trace import tracer  # type: ignore
    PHOENIX_AVAILABLE = True
except (ImportError, SyntaxError):
    PHOENIX_AVAILABLE = False
    tracer = None


def trace_function(
    name: Optional[str] = None,
    attributes: Optional[dict] = None
):
    """
    Decorator to trace function calls with Phoenix.
    
    Usage:
        @trace_function(name="calculate_baseline", attributes={"engine": "forecast"})
        def calculate_baseline(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = name or f"{func.__module__}.{func.__name__}"
            attrs = attributes or {}
            
            start_time = time.time()
            
            # Log function call
            logger.info(f"Calling {func_name} with args={args}, kwargs={kwargs}")
            
            try:
                if PHOENIX_AVAILABLE and tracer:
                    with tracer.start_as_current_span(
                        func_name,
                        attributes={
                            "function.name": func_name,
                            "function.module": func.__module__,
                            **attrs
                        }
                    ):
                        result = func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                elapsed = time.time() - start_time
                logger.info(f"{func_name} completed in {elapsed:.3f}s")
                
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"{func_name} failed after {elapsed:.3f}s: {str(e)}",
                    exc_info=True
                )
                raise
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = name or f"{func.__module__}.{func.__name__}"
            attrs = attributes or {}
            
            start_time = time.time()
            
            logger.info(f"Calling {func_name} (async)")
            
            try:
                if PHOENIX_AVAILABLE and tracer:
                    with tracer.start_as_current_span(
                        func_name,
                        attributes={
                            "function.name": func_name,
                            "function.module": func.__module__,
                            **attrs
                        }
                    ):
                        result = await func(*args, **kwargs)
                else:
                    result = await func(*args, **kwargs)
                
                elapsed = time.time() - start_time
                logger.info(f"{func_name} completed in {elapsed:.3f}s")
                
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"{func_name} failed after {elapsed:.3f}s: {str(e)}",
                    exc_info=True
                )
                raise
        
        if iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@contextmanager
def trace_context(name: str, attributes: Optional[dict] = None):
    """
    Context manager for tracing code blocks.
    
    Usage:
        with trace_context("data_processing", {"file": "sales.xlsb"}):
            process_file()
    """
    attrs = attributes or {}
    start_time = time.time()
    
    logger.info(f"Starting {name}")
    
    try:
        if PHOENIX_AVAILABLE and tracer:
            with tracer.start_as_current_span(name, attributes=attrs):
                yield
        else:
            yield
    finally:
        elapsed = time.time() - start_time
        logger.info(f"{name} completed in {elapsed:.3f}s")


def log_metric(name: str, value: float, tags: Optional[dict] = None):
    """
    Log a metric for monitoring.
    
    Usage:
        log_metric("scenario.evaluation.time", 0.5, {"scenario_id": "123"})
    """
    tags_str = ", ".join(f"{k}={v}" for k, v in (tags or {}).items())
    logger.info(f"METRIC {name}={value} {tags_str}")
    
    # In production, send to metrics system (Prometheus, Datadog, etc.)
    # For now, just log


def log_event(event_name: str, attributes: Optional[dict] = None):
    """
    Log a business event.
    
    Usage:
        log_event("scenario.created", {"scenario_id": "123", "user": "user@example.com"})
    """
    attrs_str = ", ".join(f"{k}={v}" for k, v in (attributes or {}).items())
    logger.info(f"EVENT {event_name} {attrs_str}")
