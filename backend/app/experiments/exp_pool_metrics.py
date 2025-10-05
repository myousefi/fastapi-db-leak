from fastapi import APIRouter
from pydantic import BaseModel

from app.core.pool import get_pool_snapshot

router = APIRouter(prefix="/exp/pool", tags=["experiments"])


class PoolStats(BaseModel):
    in_use: int
    checkouts: int
    checkins: int
    max_concurrent: int
    average_hold_seconds: float | None
    in_flight_holds: list[float]


@router.get("/stats", response_model=PoolStats)
def pool_stats() -> PoolStats:
    snapshot = get_pool_snapshot()
    if snapshot is None:
        return PoolStats(
            in_use=0,
            checkouts=0,
            checkins=0,
            max_concurrent=0,
            average_hold_seconds=None,
            in_flight_holds=[],
        )
    return PoolStats(
        in_use=snapshot.checked_out_now,
        checkouts=snapshot.total_checkouts,
        checkins=snapshot.total_checkins,
        max_concurrent=snapshot.max_concurrent,
        average_hold_seconds=snapshot.average_hold_seconds,
        in_flight_holds=snapshot.in_flight_holds,
    )
