"""
AURORA-SWING

Dynamic Position Sizing Engine
==============================

Capital allocation is never fixed-share. Size adapts to volatility, model
confidence, regime and the risk budget:

    Position = RiskCapital / StopDistance
"""

from __future__ import annotations

__all__ = ["PositionSizer"]


class PositionSizer:
    """Risk-based share sizing capped at a per-trade risk budget."""

    def __init__(self, max_risk_per_trade: float = 0.02) -> None:
        self.max_risk = max_risk_per_trade

    def calculate(
        self,
        capital: float,
        entry_price: float,
        stop_price: float,
        confidence: float,
        regime_multiplier: float = 1.0,
    ) -> int:
        """Return the number of shares to trade for the given risk inputs."""
        risk_amount = capital * self.max_risk * confidence * regime_multiplier

        stop_distance = abs(entry_price - stop_price)
        if stop_distance == 0:
            return 0

        shares = risk_amount / stop_distance
        return int(shares)
