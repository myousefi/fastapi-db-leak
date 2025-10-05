import os
from contextlib import asynccontextmanager

import anyio
from fastapi import FastAPI

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


@app.get("/healthz")
def healthz() -> dict[str, bool]:
    return {"ok": True}
