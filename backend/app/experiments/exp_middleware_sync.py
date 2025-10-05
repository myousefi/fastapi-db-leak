from collections.abc import Callable

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models import Item, User

router = APIRouter(prefix="/api/v1/exp/mw-sync", tags=["experiments"])
router_leak = APIRouter(prefix="/api/v1/exp/mw-sync-leak", tags=["experiments"])


class Filters(BaseModel):
    total_users: int
    active_users: int
    total_items: int


def _query_filters(db: Session) -> Filters:
    total_users = int(db.execute(select(func.count()).select_from(User)).scalar_one())
    active_users = int(
        db.execute(
            select(func.count()).select_from(User).where(User.is_active.is_(True))
        ).scalar_one()
    )
    total_items = int(db.execute(select(func.count()).select_from(Item)).scalar_one())
    return Filters(
        total_users=total_users,
        active_users=active_users,
        total_items=total_items,
    )


def install_middleware(app) -> None:
    @app.middleware("http")
    async def middleware_good(request: Request, call_next: Callable):
        if request.url.path.startswith("/api/v1/exp/mw-sync/"):
            session = SessionLocal()
            try:
                request.state.db = session
                response = await call_next(request)
                return response
            finally:
                session.close()
        return await call_next(request)

    @app.middleware("http")
    async def middleware_leak(request: Request, call_next: Callable):
        if request.url.path.startswith("/api/v1/exp/mw-sync-leak/"):
            request.state.db = SessionLocal()
            return await call_next(request)
        return await call_next(request)


@router.get("/filters", response_model=Filters)
def mw_good(request: Request) -> Filters:
    _require_bearer(request)
    return _query_filters(request.state.db)


@router_leak.get("/filters", response_model=Filters)
def mw_leak(request: Request) -> Filters:
    _require_bearer(request)
    return _query_filters(request.state.db)
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
