"""Module 10 — deployment (torch-free parts: signals + monitoring)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from helpers import load_module


class _Scalar:
    """Minimal stand-in for a 0-d tensor exposing ``.item()``."""

    def __init__(self, value: float) -> None:
        self._value = value

    def item(self) -> float:
        return self._value


class _Regime(Enum):
    BULL_TREND = 1


def _analysis(uncertainty: float, approved: bool) -> dict:
    action = [_Scalar(1), _Scalar(0.25), _Scalar(0.02), _Scalar(0.06)]
    return {
        "raw_action": action,
        "regime": {"regime": _Regime.BULL_TREND},
        "risk": {"approved": approved},
        "world": {"uncertainty": _Scalar(uncertainty)},
    }


def test_signal_generator_builds_trading_signal() -> None:
    m = load_module("10_deployment/signal_service.py", "signal_service")
    sig = m.SignalGenerator().generate("NVDA", _analysis(0.3, True))
    assert sig.symbol == "NVDA"
    assert sig.direction == 1
    assert abs(sig.confidence - 0.7) < 1e-9
    assert sig.regime == "BULL_TREND"
    assert sig.approved is True
    assert isinstance(sig.timestamp, datetime)
    assert isinstance(sig.to_dict()["timestamp"], str)


def test_signal_confidence_is_clamped() -> None:
    m = load_module("10_deployment/signal_service.py", "signal_service")
    sig = m.SignalGenerator().generate("AAPL", _analysis(1.4, False))
    assert sig.confidence == 0.0
    assert sig.approved is False


def test_model_monitor_health() -> None:
    m = load_module("10_deployment/monitoring.py", "monitoring")
    mon = m.ModelMonitor()
    assert mon.check_health({"drawdown": 0.05, "uncertainty": 0.4, "reward_decay": 0.05, "drift": 0.1}) == []
    alerts = mon.check_health({"drawdown": 0.30, "uncertainty": 0.9, "reward_decay": 0.5, "drift": 0.5})
    assert "MAX_DRAWDOWN_WARNING" in alerts
    assert "MODEL_UNCERTAINTY_HIGH" in alerts
    assert "PERFORMANCE_DEGRADATION" in alerts
    assert mon.check_health({}) == []  # missing metrics default to 0


def test_model_monitor_custom_thresholds() -> None:
    m = load_module("10_deployment/monitoring.py", "monitoring")
    thresholds = m.HealthThresholds()
    thresholds.MAX_DRAWDOWN = 0.05
    mon = m.ModelMonitor(thresholds)
    assert "MAX_DRAWDOWN_WARNING" in mon.check_health({"drawdown": 0.06})
