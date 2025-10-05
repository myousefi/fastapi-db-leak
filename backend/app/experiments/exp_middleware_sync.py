from collections.abc import Callable

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlmodel import Session, func, select

from app.core.db import engine
from app.models import Item, User

router = APIRouter(prefix="/exp/mw-sync", tags=["experiments"])
router_leak = APIRouter(prefix="/exp/mw-sync-leak", tags=["experiments"])


class Filters(BaseModel):
    total_users: int
    active_users: int
    total_items: int


def _query_filters(db: Session) -> Filters:
    total_users = int(db.exec(select(func.count()).select_from(User)).one())
    active_users = int(
        db.exec(select(func.count()).select_from(User).where(User.is_active)).one()
    )
    total_items = int(db.exec(select(func.count()).select_from(Item)).one())
    return Filters(
        total_users=total_users,
        active_users=active_users,
        total_items=total_items,
    )


def install_middleware(app) -> None:
    @app.middleware("http")
    async def middleware_good(request: Request, call_next: Callable):
        if request.url.path.startswith("/exp/mw-sync/"):
            session = Session(engine)
            try:
                request.state.db = session
                response = await call_next(request)
                return response
            finally:
                session.close()
        return await call_next(request)

    @app.middleware("http")
    async def middleware_leak(request: Request, call_next: Callable):
        if request.url.path.startswith("/exp/mw-sync-leak/"):
            request.state.db = Session(engine)
            return await call_next(request)
        return await call_next(request)


@router.get("/filters", response_model=Filters)
def mw_good(request: Request) -> Filters:
    return _query_filters(request.state.db)


@router_leak.get("/filters", response_model=Filters)
def mw_leak(request: Request) -> Filters:
    return _query_filters(request.state.db)
