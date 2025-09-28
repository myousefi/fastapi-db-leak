"""Connection pool instrumentation for the db leak experiments.

This module hooks into SQLAlchemy's pool events to keep extremely light-weight
metrics about how connections are used while the experiments run.  The
instrumentation intentionally avoids any heavy locking so it can be enabled in
the local demo stack without skewing results.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine


@dataclass
class PoolSnapshot:
    """Serializable view of the current pool state."""

    checked_out_now: int
    total_checkouts: int
    total_checkins: int
    max_concurrent: int
    average_hold_seconds: float | None
    in_flight_holds: list[float]


class PoolMetrics:
    """Tracks pool activity for debugging connection lifetime issues."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._checked_out_now = 0
        self._total_checkouts = 0
        self._total_checkins = 0
        self._max_concurrent = 0
        self._total_hold_time = 0.0
        self._hold_samples = 0
        self._active: dict[int, float] = {}

    # SQLAlchemy event handlers -------------------------------------------------
    def _on_checkout(  # type: ignore[override]
        self,
        dbapi_connection: Any,
        connection_record: Any,
        connection_proxy: Any,
    ) -> None:
        checkout_started = monotonic()
        record_id = id(connection_record)
        with self._lock:
            self._total_checkouts += 1
            self._checked_out_now += 1
            if self._checked_out_now > self._max_concurrent:
                self._max_concurrent = self._checked_out_now
            self._active[record_id] = checkout_started

    def _on_checkin(  # type: ignore[override]
        self,
        dbapi_connection: Any,
        connection_record: Any,
    ) -> None:
        record_id = id(connection_record)
        hold_started = None
        with self._lock:
            self._total_checkins += 1
            if self._checked_out_now > 0:
                self._checked_out_now -= 1
            hold_started = self._active.pop(record_id, None)

        if hold_started is not None:
            hold_duration = monotonic() - hold_started
            with self._lock:
                self._total_hold_time += hold_duration
                self._hold_samples += 1

    # Public API ----------------------------------------------------------------
    def snapshot(self) -> PoolSnapshot:
        with self._lock:
            average_hold = (
                self._total_hold_time / self._hold_samples
                if self._hold_samples
                else None
            )
            in_flight = [monotonic() - started for started in self._active.values()]

            return PoolSnapshot(
                checked_out_now=self._checked_out_now,
                total_checkouts=self._total_checkouts,
                total_checkins=self._total_checkins,
                max_concurrent=self._max_concurrent,
                average_hold_seconds=average_hold,
                in_flight_holds=in_flight,
            )


def instrument_engine(engine: Engine) -> PoolMetrics:
    """Attach the event listeners to ``engine`` and return the metrics handle."""

    metrics = PoolMetrics()
    event.listen(engine, "checkout", metrics._on_checkout, retval=False)
    event.listen(engine, "checkin", metrics._on_checkin)
    return metrics


pool_metrics: PoolMetrics | None = None


def set_pool_metrics(metrics: PoolMetrics) -> None:
    global pool_metrics
    pool_metrics = metrics


def get_pool_snapshot() -> PoolSnapshot | None:
    metrics = pool_metrics
    if metrics is None:
        return None
    return metrics.snapshot()
