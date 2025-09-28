from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.api import deps
from app.core.db import engine
from app.core.pool import get_pool_snapshot
from app.services.incentive_discovery import (
    IncentiveDiscoveryService,
    IncentiveSearchQueryFilters,
)

experiment_router = APIRouter(
    prefix="/experiments/connection-lifetime",
    tags=["connection-lifetime"],
)
router = APIRouter()


def _run_filters(db: Session) -> IncentiveSearchQueryFilters:
    return IncentiveDiscoveryService(db=db).get_filters()


@experiment_router.get("/filters-di", response_model=IncentiveSearchQueryFilters)
def get_filters_di(
    ctx: deps.UserContext = Depends(deps.get_current_active_user_context),
) -> IncentiveSearchQueryFilters:
    return _run_filters(ctx.db)


@experiment_router.get("/filters-inline", response_model=IncentiveSearchQueryFilters)
def get_filters_inline(request: Request) -> IncentiveSearchQueryFilters:
    token = deps.extract_bearer_token(request)
    with Session(engine) as session:
        ctx = deps.build_user_context(session, token)
        return _run_filters(ctx.db)


@experiment_router.get("/filters-di-noquery", response_model=IncentiveSearchQueryFilters)
def get_filters_di_noquery(
    identity: deps.UserIdentity = Depends(deps.get_current_user_identity),
) -> IncentiveSearchQueryFilters:
    with Session(engine) as session:
        ctx = deps.build_user_context_from_identity(session, identity)
        return _run_filters(ctx.db)


@experiment_router.get(
    "/filters-inline-mw",
    response_model=IncentiveSearchQueryFilters,
    dependencies=[Depends(deps.pre_handler_connection_probe)],
)
def get_filters_inline_with_middleware(request: Request) -> IncentiveSearchQueryFilters:
    token = deps.extract_bearer_token(request)
    with Session(engine) as session:
        ctx = deps.build_user_context(session, token)
        return _run_filters(ctx.db)


@router.get("/_pool", tags=["pool"])
def get_pool_state() -> dict[str, object]:
    snapshot = get_pool_snapshot()
    if snapshot is None:
        return {"available": False}
    return {
        "available": True,
        "checked_out_now": snapshot.checked_out_now,
        "total_checkouts": snapshot.total_checkouts,
        "total_checkins": snapshot.total_checkins,
        "max_concurrent": snapshot.max_concurrent,
        "average_hold_seconds": snapshot.average_hold_seconds,
        "in_flight_holds": snapshot.in_flight_holds,
    }


router.include_router(experiment_router)
