"""
AURORA-SWING

Overnight Gap Risk Model
========================

Swing trading carries a unique danger: exposure while the market is closed
(earnings, geopolitical events, macro releases, unexpected news). This model
estimates overnight movement and returns a size multiplier that throttles
exposure when gap risk is elevated.
"""

from __future__ import annotations

__all__ = ["GapRiskModel"]


class GapRiskModel:
    """Estimate overnight gap magnitude and the size multiplier it implies."""

    def __init__(self, max_expected_gap: float = 0.05) -> None:
        self.max_gap = max_expected_gap

    def expected_gap(self, volatility: float, vix: float) -> float:
        """Estimate overnight movement from volatility and VIX."""
        return volatility * (1 + vix / 100)

    def risk_multiplier(self, expected_gap: float) -> float:
        """Throttle size as the expected gap grows."""
        if expected_gap > self.max_gap:
            return 0.25
        if expected_gap > 0.03:
            return 0.50
        return 1.0
