import logging
import sys
import os
import structlog
from contextvars import ContextVar
from typing import Optional

# Context variable for request ID
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return request_id_ctx.get()


def setup_logging(log_level: str = "INFO", json_format: bool = True) -> None:
    """
    Configure structured logging with Google Cloud Logging integration.

    In production (Cloud Run), logs are formatted for Cloud Logging.
    Locally, logs use colored console output.
    """
    # Detect if running on GCP (Cloud Run sets these env vars)
    is_gcp = os.getenv("K_SERVICE") is not None or os.getenv("GOOGLE_CLOUD_PROJECT") is not None

    if is_gcp:
        _setup_cloud_logging(log_level)
    else:
        _setup_local_logging(log_level, json_format)


def _setup_cloud_logging(log_level: str) -> None:
    """Configure logging for Google Cloud Run with Cloud Logging integration."""
    import google.cloud.logging
    from google.cloud.logging_v2.handlers import StructuredLogHandler

    # Initialize Cloud Logging client
    client = google.cloud.logging.Client()

    # Create a handler that formats logs for Cloud Logging
    handler = StructuredLogHandler(stream=sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.handlers = []
    root_logger.addHandler(handler)

    # Configure structlog to work with Cloud Logging
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            _add_cloud_logging_context,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _setup_local_logging(log_level: str, json_format: bool) -> None:
    """Configure logging for local development."""
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_format:
        structlog.configure(
            processors=shared_processors
            + [
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, log_level.upper())
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        structlog.configure(
            processors=shared_processors
            + [
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, log_level.upper())
            ),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )


def _add_cloud_logging_context(
    logger: logging.Logger, method_name: str, event_dict: dict
) -> dict:
    """
    Add Google Cloud Logging specific fields.

    Cloud Logging recognizes these special fields:
    - severity: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - logging.googleapis.com/trace: Trace ID for request correlation
    - logging.googleapis.com/labels: Custom labels for filtering
    """
    # Map log level to Cloud Logging severity
    level = event_dict.get("level", "info").upper()
    event_dict["severity"] = level

    # Add request ID as trace if available
    request_id = get_request_id()
    if request_id:
        project_id = os.getenv("GCP_PROJECT_ID", "")
        if project_id:
            event_dict["logging.googleapis.com/trace"] = f"projects/{project_id}/traces/{request_id}"
        event_dict["request_id"] = request_id

    # Add labels for better filtering in Cloud Logging
    event_dict["logging.googleapis.com/labels"] = {
        "service": os.getenv("K_SERVICE", "flexbone-ocr-api"),
        "revision": os.getenv("K_REVISION", "local"),
    }

    return event_dict


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a logger instance with optional name binding"""
    logger = structlog.get_logger()
    if name:
        logger = logger.bind(logger_name=name)
    return logger


class CloudLoggingMiddleware:
    """
    Middleware to add Cloud Logging trace context to requests.

    Extracts trace ID from X-Cloud-Trace-Context header and adds it to logs.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            trace_header = headers.get(b"x-cloud-trace-context", b"").decode()

            if trace_header:
                # Format: TRACE_ID/SPAN_ID;o=TRACE_TRUE
                trace_id = trace_header.split("/")[0]
                structlog.contextvars.bind_contextvars(trace_id=trace_id)

        await self.app(scope, receive, send)
