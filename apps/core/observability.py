"""
Observability utilities for structured logging and tracing.
Provides JSON logging, request correlation, and OpenTelemetry tracing with safe fallbacks.
"""
import logging
import json
import uuid
import time
import contextvars
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable for request ID
request_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add request_id if available in context
        request_id = request_id_ctx.get()
        if request_id:
            log_data["request_id"] = request_id
        
        # Add custom data if present (for access logging)
        if hasattr(record, "custom_log_data"):
            log_data.update(record.custom_log_data)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured JSON logging."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Remove any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Create console handler with JSON formatter
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    handler.setLevel(level)
    
    root_logger.setLevel(level)
    root_logger.addHandler(handler)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add X-Request-ID header and correlation."""
    
    async def dispatch(self, request: Request, call_next):
        # Get existing request ID or generate new one
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Store in context
        token = request_id_ctx.set(request_id)
        
        # Start timing
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            # Log structured access log using the access logger
            access_logger = logging.getLogger("access")
            access_logger.info(
                "HTTP request completed",
                extra={
                    "custom_log_data": {
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "latency_ms": round(latency_ms, 2),
                        "request_id": request_id,
                    }
                }
            )
            
            return response
        finally:
            # Reset context
            request_id_ctx.reset(token)


def init_tracing(app) -> None:
    """
    Initialize OpenTelemetry tracing with safe fallbacks.
    Only enables OTLP export when OTEL_EXPORTER_OTLP_ENDPOINT is set.
    Uses manual span creation to avoid auto-instrumentation dependencies.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        import os
        
        # Create resource with service name
        resource = Resource.create({
            SERVICE_NAME: "aifp-aos-api"
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Check if OTLP endpoint is configured
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        
        if otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
                provider.add_span_processor(SimpleSpanProcessor(exporter))
                logging.info(f"OpenTelemetry OTLP tracing enabled: {otlp_endpoint}")
            except ImportError:
                logging.warning("OTLP exporter not available, falling back to console export")
                provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        else:
            # Use console exporter (no-op for production without collector)
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
            logging.info("OpenTelemetry tracing enabled (console export only)")
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        # Store tracer for manual span creation
        app.state.tracer = trace.get_tracer(__name__)
        
    except ImportError as e:
        logging.warning(f"OpenTelemetry packages not available: {e}. Tracing disabled.")
    except Exception as e:
        logging.warning(f"Failed to initialize OpenTelemetry tracing: {e}. Tracing disabled.")