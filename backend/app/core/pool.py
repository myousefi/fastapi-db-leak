"""Connection pool instrumentation for the db leak experiments.

This module hooks into SQLAlchemy's pool events to keep extremely light-weight
metrics about how connections are used while the experiments run.  The
instrumentation intentionally avoids any heavy locking so it can be enabled in
the local demo stack without skewing results.
"""

from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine


@dataclass
class PoolSnapshot:
    """Serializable view of the current pool state."""

    checked_out_now: int
    total_checkouts: int
    total_checkins: int
    max_concurrent: int
    total_hold_time: float
    hold_samples: int
    average_hold_seconds: float | None
    in_flight_holds: list[float]

    def merge(self, other: "PoolSnapshot") -> "PoolSnapshot":
        total_hold_time = self.total_hold_time + other.total_hold_time
        hold_samples = self.hold_samples + other.hold_samples
        average = (
            total_hold_time / hold_samples
            if hold_samples
            else None
        )
        return PoolSnapshot(
            checked_out_now=self.checked_out_now + other.checked_out_now,
            total_checkouts=self.total_checkouts + other.total_checkouts,
            total_checkins=self.total_checkins + other.total_checkins,
            max_concurrent=max(self.max_concurrent, other.max_concurrent),
            total_hold_time=total_hold_time,
            hold_samples=hold_samples,
            average_hold_seconds=average,
            in_flight_holds=[*self.in_flight_holds, *other.in_flight_holds],
        )


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
                total_hold_time=self._total_hold_time,
                hold_samples=self._hold_samples,
                average_hold_seconds=average_hold,
                in_flight_holds=in_flight,
            )


def instrument_engine(engine: Engine) -> PoolMetrics:
    """Attach the event listeners to ``engine`` and return the metrics handle."""

    metrics = PoolMetrics()
    event.listen(engine, "checkout", metrics._on_checkout, retval=False)
    event.listen(engine, "checkin", metrics._on_checkin)
    return metrics


_sync_metrics: PoolMetrics | None = None
_async_metrics: PoolMetrics | None = None


def set_pool_metrics_for_sync(metrics: PoolMetrics) -> None:
    global _sync_metrics
    _sync_metrics = metrics


def set_pool_metrics_for_async(metrics: PoolMetrics) -> None:
    global _async_metrics
    _async_metrics = metrics


def instrument_async_engine(engine: AsyncEngine) -> PoolMetrics:
    """Instrument an async engine by wiring into its sync driver."""

    return instrument_engine(engine.sync_engine)


def get_pool_snapshot() -> PoolSnapshot | None:
    snapshots: list[PoolSnapshot] = []

    if _sync_metrics is not None:
        snapshots.append(_sync_metrics.snapshot())

    if _async_metrics is not None:
        snapshots.append(_async_metrics.snapshot())

    if not snapshots:
        return None

    merged = snapshots[0]
    for snapshot in snapshots[1:]:
        merged = merged.merge(snapshot)

    return merged
