# FastAPI Connection Lifetime Experiments

This repository is a focused playground for measuring how different FastAPI + SQLAlchemy patterns interact with PostgreSQL connection pooling. It contains only the pieces required to spin up experiments, capture telemetry, and replay load tests.

## What’s Included

- FastAPI ASGI app (`backend/app/main_experiments.py`) that exposes the experiment endpoints under `/exp/...`.
- SQLAlchemy models (`backend/app/models.py`) plus synchronous/async session helpers.
- Minimal observability hooks that push traces and logs to an OTLP collector (e.g. SigNoz).
- Make targets for running the app (locally or via Docker Compose) and sweeping concurrency with [`hey`](https://github.com/rakyll/hey).
- CSV parser for turning `hey` outputs into spreadsheets for plotting.

## Quick Start

1. Copy `.env.example` to `.env` and update the Postgres + OTLP settings.
2. Bring up Postgres and the experiment API inside Docker:
   ```bash
   make compose-up
   ```
3. Warm the endpoints and run the default sweep matrix (adjust `CONC`, `ENDPOINTS`, etc. as needed):
   ```bash
   make warmup
   make sweep-all
   ```
4. Convert the generated logs into a CSV summary:
   ```bash
   make parse PARSE_DIR=<logs/<timestamp>>
   ```

## Architecture Notes

- Synchronous experiments use a single SQLAlchemy `SessionLocal` dependency; async variants rely on `create_async_engine` + `async_sessionmaker`.
- `/exp/*` endpoints deliberately cover “good” and “bad” patterns (inline context managers, dependency injection cache misuse, middleware leaks, async loop blocking, etc.).
- `backend/app/backend_pre_start.py` waits for Postgres and calls `Base.metadata.create_all()` so the schema is always present before the app boots.
- OpenTelemetry exporters are enabled through environment variables (`OTEL_TRACING_ENABLED`, `OTEL_LOGS_ENABLED`, etc.). When pointing at SigNoz, ensure the backend container can resolve `host.docker.internal`.

## Useful Commands

- `make compose-logs` – follow the FastAPI container logs.
- `make compose-down` – stop the stack and clean up containers.
- `make sweep EP=/exp/async/loop-blocking CONC="10 50 100"` – sweep a single endpoint with a custom concurrency grid.
- `ANYIO_TOKENS=200 make compose-up` – override the threadpool tokens for sync experiments.

That’s it—clone, tweak, and run experiments.
