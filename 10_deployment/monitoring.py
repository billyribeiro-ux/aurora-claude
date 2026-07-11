"""
AURORA-SWING

Production Monitoring System
============================

Autonomous health monitoring. The system watches itself and raises alerts
before small problems become account-ending ones.

Tracks:
    * prediction confidence / model uncertainty
    * model drift
    * reward decay (performance degradation)
    * drawdown
    * abnormal behaviour (via the event log)

The monitor is intentionally simple and dependency-free so it can run inside
the hot inference loop without side effects.
"""

from __future__ import annotations

import time
from typing import Any

__all__ = ["HealthThresholds", "ModelMonitor"]


class HealthThresholds:
    """Alert thresholds. Override on an instance to tune sensitivity."""

    MAX_DRAWDOWN: float = 0.15
    MAX_UNCERTAINTY: float = 0.80
    MAX_REWARD_DECAY: float = 0.20
    MAX_DRIFT: float = 0.30


# Mapping of alert code -> (metric key, threshold attribute) used by
# check_health. Keeping this declarative makes it trivial to add new checks.
_CHECKS: tuple[tuple[str, str, str], ...] = (
    ("MAX_DRAWDOWN_WARNING", "drawdown", "MAX_DRAWDOWN"),
    ("MODEL_UNCERTAINTY_HIGH", "uncertainty", "MAX_UNCERTAINTY"),
    ("PERFORMANCE_DEGRADATION", "reward_decay", "MAX_REWARD_DECAY"),
    ("MODEL_DRIFT_DETECTED", "drift", "MAX_DRIFT"),
)


class ModelMonitor:
    """Collect events and evaluate system health against thresholds."""

    def __init__(self, thresholds: HealthThresholds | None = None) -> None:
        self.thresholds = thresholds or HealthThresholds()
        self.events: list[dict[str, Any]] = []

    def log(self, event: Any) -> dict[str, Any]:
        """Append a timestamped ``event`` to the event log and return it."""
        record = {"time": time.time(), "event": event}
        self.events.append(record)
        return record

    def check_health(self, metrics: dict[str, float]) -> list[str]:
        """Return a list of alert codes for any breached threshold.

        Unknown / missing metrics are treated as ``0.0`` so a partial metrics
        dict never crashes the monitor. An empty list means the system is
        healthy.
        """
        alerts: list[str] = []
        for code, metric_key, threshold_attr in _CHECKS:
            value = float(metrics.get(metric_key, 0.0))
            limit = float(getattr(self.thresholds, threshold_attr))
            if value > limit:
                alerts.append(code)

        if alerts:
            self.log({"health_alerts": alerts, "metrics": dict(metrics)})

        return alerts
