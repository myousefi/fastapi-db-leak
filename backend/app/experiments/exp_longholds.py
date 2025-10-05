import time

from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import Session, func, select

from app.core.db import engine
from app.models import User

router = APIRouter(prefix="/exp/longhold", tags=["experiments"])


class HoldResult(BaseModel):
    held_seconds: int
    users: int


@router.get("/{seconds}", response_model=HoldResult)
def long_hold(seconds: int) -> HoldResult:
    with Session(engine) as session:
        users = int(session.exec(select(func.count()).select_from(User)).one())
        time.sleep(max(0, seconds))
        return HoldResult(held_seconds=seconds, users=users)
