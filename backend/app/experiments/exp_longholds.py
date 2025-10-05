import time

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models import User

router = APIRouter(prefix="/exp/longhold", tags=["experiments"])


class HoldResult(BaseModel):
    held_seconds: int
    users: int


@router.get("/{seconds}", response_model=HoldResult)
def long_hold(seconds: int) -> HoldResult:
    with SessionLocal() as session:
        users = int(
            session.execute(select(func.count()).select_from(User)).scalar_one()
        )
        time.sleep(max(0, seconds))
        return HoldResult(held_seconds=seconds, users=users)
