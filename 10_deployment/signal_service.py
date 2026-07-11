"""
AURORA-SWING

Trading Signal Service
======================

Turns a raw engine ``analysis`` record into a structured, serialisable
``TradingSignal``.

A professional system deliberately separates the concerns:

    Research  ->  Signal  ->  Risk  ->  Execution

This module owns the *Signal* stage. It performs no I/O and never places an
order; it only translates an analysis into a well-typed decision object that
the execution layer (or an API / dashboard) can consume.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

__all__ = ["TradingSignal", "SignalGenerator"]


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamp ``value`` into the inclusive ``[low, high]`` range."""
    return max(low, min(high, value))


@dataclass(frozen=True, slots=True)
class TradingSignal:
    """A structured trading decision emitted by AURORA-SWING.

    Attributes
    ----------
    symbol:
        Instrument ticker (e.g. ``"NVDA"``).
    timestamp:
        UTC timestamp at which the signal was generated.
    direction:
        ``+1`` long, ``-1`` short, ``0`` flat / no trade.
    confidence:
        Calibrated confidence in ``[0, 1]`` derived from world-model
        uncertainty (``1 - uncertainty``).
    position_size:
        Fraction of risk budget to allocate (already risk-adjusted upstream).
    stop_distance:
        Protective stop distance (in the model's normalised units).
    target_distance:
        Profit-target distance (in the model's normalised units).
    regime:
        Name of the detected market regime.
    approved:
        Final decision of the risk firewall. A signal with ``approved=False``
        must never reach the execution layer.
    """

    symbol: str
    timestamp: datetime
    direction: int
    confidence: float
    position_size: float
    stop_distance: float
    target_distance: float
    regime: str
    approved: bool

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dict (timestamp rendered as ISO-8601)."""
        payload = asdict(self)
        payload["timestamp"] = self.timestamp.isoformat()
        return payload


class SignalGenerator:
    """Convert an engine analysis record into a :class:`TradingSignal`."""

    def generate(self, symbol: str, analysis: dict[str, Any]) -> TradingSignal:
        """Build a :class:`TradingSignal` for ``symbol`` from ``analysis``.

        Parameters
        ----------
        symbol:
            The instrument the analysis refers to.
        analysis:
            The ``{"raw_action", "regime", "risk", "world"}`` record produced
            by :meth:`AuroraLiveEngine.analyze_market`.
        """
        action = analysis["raw_action"]
        regime = analysis["regime"]
        risk = analysis["risk"]

        uncertainty = float(analysis["world"]["uncertainty"].item())

        return TradingSignal(
            symbol=symbol,
            timestamp=datetime.now(timezone.utc),
            direction=int(action[0].item()),
            confidence=_clamp(1.0 - uncertainty),
            position_size=float(action[1].item()),
            stop_distance=float(action[2].item()),
            target_distance=float(action[3].item()),
            regime=regime["regime"].name,
            approved=bool(risk["approved"]),
        )
