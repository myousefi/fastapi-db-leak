from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlmodel import Session, func, select
from sqlmodel.ext.asyncio.session import AsyncSession, async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.db import engine as sync_engine
from app.models import Item, User

router = APIRouter(prefix="/exp/async", tags=["experiments"])


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


async def get_async_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


async def _async_filters(db: AsyncSession) -> Filters:
    total_users = int((await db.exec(select(func.count()).select_from(User))).one())
    active_users = int(
        (
            await db.exec(
                select(func.count()).select_from(User).where(User.is_active)
            )
        ).one()
    )
    total_items = int((await db.exec(select(func.count()).select_from(Item))).one())
    return Filters(
        total_users=total_users,
        active_users=active_users,
        total_items=total_items,
    )


@router.get("/di", response_model=Filters)
async def async_di(db: AsyncSession = Depends(get_async_db)) -> Filters:
    return await _async_filters(db)


# --- Loop-blocking pattern: sync work executed inline ------------------------
@router.get("/loop-blocking", response_model=Filters)
async def async_loop_blocking() -> Filters:
    with Session(sync_engine) as session:
        total_users = int(session.exec(select(func.count()).select_from(User)).one())
        active_users = int(
            session.exec(select(func.count()).select_from(User).where(User.is_active)).one()
        )
        total_items = int(session.exec(select(func.count()).select_from(Item)).one())
        return Filters(
            total_users=total_users,
            active_users=active_users,
            total_items=total_items,
        )


def _sync_impl() -> Filters:
    with Session(sync_engine) as session:
        total_users = int(session.exec(select(func.count()).select_from(User)).one())
        active_users = int(
            session.exec(select(func.count()).select_from(User).where(User.is_active)).one()
        )
        total_items = int(session.exec(select(func.count()).select_from(Item)).one())
        return Filters(
            total_users=total_users,
            active_users=active_users,
            total_items=total_items,
        )


@router.get("/bridge", response_model=Filters)
async def async_bridge() -> Filters:
    return await run_in_threadpool(_sync_impl)
