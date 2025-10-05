"""Tracing helpers for wiring the application with OpenTelemetry."""

import logging
from collections.abc import Iterable, Sequence

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from sqlalchemy.engine import Engine

from app.core.config import settings

_logger = logging.getLogger(__name__)

_FASTAPI_INSTRUMENTED = False
_SQLALCHEMY_INSTRUMENTED: set[int] = set()
_PROVIDER_ATTRIBUTE = "_app_instrumentation_configured"


def setup_tracing(
    app: FastAPI,
    *,
    engine: Engine,
    extra_engines: Iterable[Engine] | None = None,
) -> None:
    """Wire OpenTelemetry tracing for FastAPI requests and SQLAlchemy queries."""
    if not settings.OTEL_TRACING_ENABLED:
        _logger.debug("Skipping OpenTelemetry setup because OTEL_TRACING_ENABLED is false")
        return

    try:
        tracer_provider = _get_or_create_tracer_provider()
    except Exception:  # pragma: no cover - defensive logging
        _logger.exception("Failed to configure OpenTelemetry tracer provider")
        return

    _instrument_fastapi(app, tracer_provider)
    _instrument_sqlalchemy(engine, tracer_provider)
    if extra_engines:
        for extra in extra_engines:
            _instrument_sqlalchemy(extra, tracer_provider)


def _get_or_create_tracer_provider() -> TracerProvider:
    provider = trace.get_tracer_provider()
    if isinstance(provider, TracerProvider) and getattr(provider, _PROVIDER_ATTRIBUTE, False):
        return provider

    resource_attributes = {
        "service.name": settings.OTEL_SERVICE_NAME or settings.PROJECT_NAME,
        "deployment.environment": settings.ENVIRONMENT,
    }
    if settings.OTEL_SERVICE_VERSION:
        resource_attributes["service.version"] = settings.OTEL_SERVICE_VERSION
    resource = Resource.create(resource_attributes)

    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        headers=_parse_headers(settings.OTEL_EXPORTER_OTLP_HEADERS),
        insecure=settings.OTEL_EXPORTER_OTLP_INSECURE,
        timeout=settings.OTEL_EXPORTER_OTLP_TIMEOUT,
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    setattr(provider, _PROVIDER_ATTRIBUTE, True)
    return provider


def _instrument_fastapi(app: FastAPI, tracer_provider: TracerProvider) -> None:
    global _FASTAPI_INSTRUMENTED
    if _FASTAPI_INSTRUMENTED:
        return

    excluded_urls = settings.OTEL_FASTAPI_EXCLUDED_URLS or None

    def _server_request_hook(span, scope):  # type: ignore[no-untyped-def]
        if span is None:
            return
        route = scope.get("route")
        if route is not None and getattr(route, "path", None):
            span.set_attribute("http.route", route.path)
        else:
            path = scope.get("path")
            if path:
                span.set_attribute("http.route", path)

    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=tracer_provider,
        excluded_urls=excluded_urls,
        server_request_hook=_server_request_hook,
    )
    _FASTAPI_INSTRUMENTED = True


def _instrument_sqlalchemy(engine: Engine, tracer_provider: TracerProvider) -> None:
    sql_engine = getattr(engine, "sync_engine", engine)
    engine_id = id(sql_engine)
    if engine_id in _SQLALCHEMY_INSTRUMENTED:
        return

    SQLAlchemyInstrumentor().instrument(
        engine=sql_engine,
        tracer_provider=tracer_provider,
        enable_commenter=settings.OTEL_SQLCOMMENTER_ENABLED,
    )
    _SQLALCHEMY_INSTRUMENTED.add(engine_id)


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
