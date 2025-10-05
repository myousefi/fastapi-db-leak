from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request, status
from sqlmodel import Session, func, select

from app.core.db import engine
from app.models import Item, User

router = APIRouter(prefix="/exp/inline-sync", tags=["experiments"])


class Filters(BaseModel):
    total_users: int
    active_users: int
    total_items: int


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


def query_filters(db: Session) -> Filters:
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


@router.get("/filters", response_model=Filters)
def filters_inline_sync(request: Request) -> Filters:
    _ = extract_bearer_token(request)
    with Session(engine) as session:
        return query_filters(session)
