"""Logging helpers for exporting application logs via OpenTelemetry."""

import logging
from collections.abc import Iterable, Sequence

from opentelemetry._logs import get_logger_provider, set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

from app.core.config import settings

_logger = logging.getLogger(__name__)

_PROVIDER_ATTRIBUTE = "_app_logging_configured"
_HANDLER_NAME = "opentelemetry-otlp-log-handler"


def setup_logging() -> None:
    """Attach an OTLP log handler to the root logger when enabled."""
    if not settings.OTEL_LOGS_ENABLED:
        _logger.debug("Skipping OpenTelemetry log setup because OTEL_LOGS_ENABLED is false")
        return

    try:
        provider = _get_or_create_logger_provider()
    except Exception:  # pragma: no cover - defensive logging
        _logger.exception("Failed to configure OpenTelemetry logger provider")
        return

    handler_level = _resolve_level(settings.OTEL_LOG_LEVEL)
    root_logger = logging.getLogger()

    if any(getattr(existing, "name", None) == _HANDLER_NAME for existing in root_logger.handlers):
        return

    handler = LoggingHandler(level=handler_level, logger_provider=provider)
    handler.set_name(_HANDLER_NAME)
    handler.setLevel(handler_level)
    root_logger.addHandler(handler)

    if root_logger.level > handler_level:
        root_logger.setLevel(handler_level)


def _resolve_level(level_name: str) -> int:
    if not level_name:
        return logging.INFO

    candidate = getattr(logging, level_name.upper(), None)
    if isinstance(candidate, int):
        return candidate

    _logger.warning("Invalid OTEL_LOG_LEVEL '%s'; defaulting to INFO", level_name)
    return logging.INFO


def _get_or_create_logger_provider() -> LoggerProvider:
    provider = get_logger_provider()
    if isinstance(provider, LoggerProvider) and getattr(provider, _PROVIDER_ATTRIBUTE, False):
        return provider

    resource = _build_resource()
    exporter = OTLPLogExporter(
        endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        headers=_parse_headers(settings.OTEL_EXPORTER_OTLP_HEADERS),
        insecure=settings.OTEL_EXPORTER_OTLP_INSECURE,
        timeout=settings.OTEL_EXPORTER_OTLP_TIMEOUT,
    )
    provider = LoggerProvider(resource=resource)
    provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    set_logger_provider(provider)
    setattr(provider, _PROVIDER_ATTRIBUTE, True)
    return provider


def _build_resource() -> Resource:
    resource_attributes = {
        "service.name": settings.OTEL_SERVICE_NAME or settings.PROJECT_NAME,
        "deployment.environment": settings.ENVIRONMENT,
    }
    if settings.OTEL_SERVICE_VERSION:
        resource_attributes["service.version"] = settings.OTEL_SERVICE_VERSION
    return Resource.create(resource_attributes)


def _parse_headers(raw_headers: str | None) -> Sequence[tuple[str, str]] | None:
    if not raw_headers:
        return None

    def _pairs() -> Iterable[tuple[str, str]]:
        for entry in raw_headers.split(","):
            key, _, value = entry.partition("=")
            key = key.strip()
            value = value.strip()
            if key and value:
                yield key, value

    headers = list(_pairs())
    return headers or None
