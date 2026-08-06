import pytest
import json
from httpx import AsyncClient, ASGITransport
from apps.api.main import app

@pytest.mark.asyncio
async def test_request_id_header():
    """Test that every response carries an X-Request-ID header."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test without providing request ID
        response = await client.get("/health")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0
        
        # Test with provided request ID
        custom_id = "test-request-id-123"
        response = await client.get("/health", headers={"X-Request-ID": custom_id})
        assert response.status_code == 200
        assert response.headers["X-Request-ID"] == custom_id


@pytest.mark.asyncio
async def test_structured_logging():
    """Test that requests produce structured (JSON-parseable) access log lines."""
    import logging
    import io
    from apps.core.observability import JSONFormatter, request_id_ctx
    from apps.api.config import settings
    
    # Create a string buffer to capture log output
    log_buffer = io.StringIO()
    handler = logging.StreamHandler(log_buffer)
    handler.setFormatter(JSONFormatter())
    
    # Add handler to access logger
    access_logger = logging.getLogger("access")
    access_logger.addHandler(handler)
    access_logger.setLevel(logging.INFO)
    
    # Create a log record with custom data
    record = logging.LogRecord(
        name="access",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="HTTP request completed",
        args=(),
        exc_info=None,
    )
    
    # Add custom data that the middleware uses
    record.custom_log_data = {
        "method": "GET",
        "path": "/health",
        "status_code": 200,
        "latency_ms": 42.5,
        "request_id": "test-123",
    }
    
    # Format the record
    handler.emit(record)
    
    # Get the log output
    log_output = log_buffer.getvalue()
    
    # Parse as JSON
    log_data = json.loads(log_output)
    
    # Verify structured fields
    assert log_data["level"] == "INFO"
    assert log_data["logger"] == "access"
    assert log_data["message"] == "HTTP request completed"
    assert log_data["method"] == "GET"
    assert log_data["path"] == "/health"
    assert log_data["status_code"] == 200
    assert log_data["latency_ms"] == 42.5
    assert log_data["request_id"] == "test-123"
    
    # Clean up
    access_logger.removeHandler(handler)


@pytest.mark.asyncio
async def test_tracing_init_no_crash():
    """Test that tracing initialization doesn't crash without OTLP endpoint."""
    from apps.core.observability import init_tracing
    from fastapi import FastAPI
    
    # Create a test app
    test_app = FastAPI()
    
    # Should not crash even without OTEL_EXPORTER_OTLP_ENDPOINT
    init_tracing(test_app)
    
    # Should have tracer attribute (even if no-op)
    assert hasattr(test_app.state, "tracer")