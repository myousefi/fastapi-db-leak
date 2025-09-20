from __future__ import annotations

from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, select

from app.models import Item, User


class IncentiveSearchQueryFilters(BaseModel):
    total_users: int
    active_users: int
    total_items: int


class IncentiveDiscoveryService:
    """Minimal service that hits the database for experiment symmetry."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_filters(self) -> IncentiveSearchQueryFilters:
        total_users = self._db.exec(
            select(func.count()).select_from(User)
        ).one()
        active_users = self._db.exec(
            select(func.count()).select_from(User).where(User.is_active)
        ).one()
        total_items = self._db.exec(
            select(func.count()).select_from(Item)
        ).one()

        return IncentiveSearchQueryFilters(
            total_users=total_users,
            active_users=active_users,
            total_items=total_items,
        )
