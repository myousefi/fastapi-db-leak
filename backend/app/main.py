import os
from contextlib import asynccontextmanager

import anyio
from fastapi import FastAPI, Request
from opentelemetry import trace

from app.experiments import (
    exp_async,
    exp_di_sync,
    exp_inline_sync,
    exp_longholds,
    exp_middleware_sync,
    exp_pool_metrics,
)
from app.core.db import engine
from app.observability.logging import setup_logging
from app.observability.tracing import setup_tracing
from app.core.pool import get_pool_snapshot


@asynccontextmanager
async def lifespan(app: FastAPI):
    tokens_raw = os.getenv("ANYIO_TOKENS", "40")
    try:
        tokens = int(tokens_raw)
    except ValueError:
        tokens = 40
    anyio.to_thread.current_default_thread_limiter().total_tokens = tokens
    yield


app = FastAPI(
    title="FastAPI connection lifetime experiments",
    lifespan=lifespan,
)

exp_middleware_sync.install_middleware(app)
app.include_router(exp_inline_sync.router)
app.include_router(exp_di_sync.router)
app.include_router(exp_middleware_sync.router)
app.include_router(exp_middleware_sync.router_leak)
app.include_router(exp_async.router)
app.include_router(exp_longholds.router)
app.include_router(exp_pool_metrics.router)

setup_logging()
setup_tracing(app, engine=engine, extra_engines=[exp_async.async_engine])


@app.middleware("http")
async def otel_pool_attrs(request: Request, call_next):
    span = trace.get_current_span()
    pre_snapshot = get_pool_snapshot()

    if span and span.is_recording() and pre_snapshot:
        span.set_attribute("pool.in_use.before", pre_snapshot.checked_out_now)
        span.set_attribute("pool.max_concurrent", pre_snapshot.max_concurrent)
        span.set_attribute(
            "pool.avg_hold_s", pre_snapshot.average_hold_seconds or 0.0
        )
        route = request.scope.get("route")
        if route and getattr(route, "path", None):
            span.set_attribute("http.route", route.path)

    response = await call_next(request)

    if span and span.is_recording():
        post_snapshot = get_pool_snapshot()
        if post_snapshot:
            span.set_attribute("pool.in_use.after", post_snapshot.checked_out_now)
            delta = post_snapshot.checked_out_now - (
                pre_snapshot.checked_out_now if pre_snapshot else 0
            )
            span.set_attribute("pool.in_use.delta", delta)

    return response


@app.get("/healthz")
def healthz() -> dict[str, bool]:
    return {"ok": True}
