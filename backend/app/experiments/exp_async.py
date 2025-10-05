from collections.abc import AsyncIterator

import anyio
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.pool import instrument_async_engine, set_pool_metrics_for_async
from app.models import Item, User

router = APIRouter(prefix="/api/v1/exp/async", tags=["experiments"])


class Filters(BaseModel):
    total_users: int
    active_users: int
    total_items: int


ASYNC_DSN = str(settings.SQLALCHEMY_DATABASE_URI).replace("+psycopg", "+asyncpg")
async_engine = create_async_engine(
    ASYNC_DSN,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)
set_pool_metrics_for_async(instrument_async_engine(async_engine))

async def get_async_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    return AsyncSessionLocal


def _require_bearer(request: Request) -> None:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def _async_filters(db: AsyncSession) -> Filters:
    total_users = int(
        (
            await db.execute(select(func.count()).select_from(User))
        ).scalar_one()
    )
    active_users = int(
        (
            await db.execute(
                select(func.count()).select_from(User).where(User.is_active.is_(True))
            )
        ).scalar_one()
    )
    total_items = int(
        (await db.execute(select(func.count()).select_from(Item))).scalar_one()
    )
    return Filters(
        total_users=total_users,
        active_users=active_users,
        total_items=total_items,
    )


@router.get("/di", response_model=Filters)
async def async_di(request: Request, db: AsyncSession = Depends(get_async_db)) -> Filters:
    _require_bearer(request)
    return await _async_filters(db)


# --- Loop-blocking pattern: sync work executed inline ------------------------
@router.get("/loop-blocking", response_model=Filters)
async def async_loop_blocking(request: Request) -> Filters:
    _require_bearer(request)
    with SessionLocal() as session:
        total_users = int(
            session.execute(select(func.count()).select_from(User)).scalar_one()
        )
        active_users = int(
            session.execute(
                select(func.count()).select_from(User).where(User.is_active.is_(True))
            ).scalar_one()
        )
        total_items = int(
            session.execute(select(func.count()).select_from(Item)).scalar_one()
        )
        return Filters(
            total_users=total_users,
            active_users=active_users,
            total_items=total_items,
        )


def _sync_impl() -> Filters:
    with SessionLocal() as session:
        total_users = int(
            session.execute(select(func.count()).select_from(User)).scalar_one()
        )
        active_users = int(
            session.execute(
                select(func.count()).select_from(User).where(User.is_active.is_(True))
            ).scalar_one()
        )
        total_items = int(
            session.execute(select(func.count()).select_from(Item)).scalar_one()
        )
        return Filters(
            total_users=total_users,
            active_users=active_users,
            total_items=total_items,
        )


@router.get("/bridge", response_model=Filters)
async def async_bridge(request: Request) -> Filters:
    _require_bearer(request)
    return await run_in_threadpool(_sync_impl)
