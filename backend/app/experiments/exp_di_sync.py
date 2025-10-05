from collections.abc import Generator
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models import Item, User

router = APIRouter(prefix="/api/v1/exp/di-sync", tags=["experiments"])


class Filters(BaseModel):
    total_users: int
    active_users: int
    total_items: int


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def extract_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if authorization is None:
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
    return token


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


# ---------------------------------------------------------------------------
# Dependency-injected sessions (good and bad patterns)
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_ctx_good(
    db: Session = Depends(get_db),
    token: str = Depends(extract_bearer_token),
) -> dict[str, object]:
    return {"db": db, "token": token}


@router.get("/good", response_model=Filters)
def di_good(ctx: dict[str, object] = Depends(get_ctx_good)) -> Filters:
    session = cast(Session, ctx["db"])
    return _query_filters(session)


def get_ctx_leak(token: str = Depends(extract_bearer_token)) -> dict[str, object]:
    session = SessionLocal()
    return {"db": session, "token": token}


@router.get("/leak", response_model=Filters)
def di_leak(ctx: dict[str, object] = Depends(get_ctx_leak)) -> Filters:
    session = cast(Session, ctx["db"])
    return _query_filters(session)


def get_db_nocache() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@router.get("/nocache", response_model=Filters)
def di_nocache(
    db1: Annotated[Session, Depends(get_db_nocache, use_cache=False)],
    db2: Annotated[Session, Depends(get_db_nocache, use_cache=False)],
) -> Filters:
    _ = db2  # second checkout triggers additional pool pressure intentionally
    return _query_filters(db1)


@router.get("/manual-next", response_model=Filters)
def di_manual_next() -> Filters:
    gen = get_db()
    _LEAKY_GENERATORS.append(gen)
    db = next(gen)
    # Returning without closing the generator simulates the leak caused by manual iteration.
    return _query_filters(db)
_LEAKY_GENERATORS: list[Generator[Session, None, None]] = []
