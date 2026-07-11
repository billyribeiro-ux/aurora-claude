"""
AURORA-SWING

Execution Simulator
===================

Models realistic order execution: fill uncertainty, volatility- and
liquidity-scaled slippage, and overnight gap risk.
"""

from __future__ import annotations

from typing import Any

import numpy as np

__all__ = ["ExecutionSimulator"]


class ExecutionSimulator:
    """Simulate fills with slippage, partial-fill probability and gaps."""

    def __init__(self, fill_probability: float = 0.98) -> None:
        self.fill_probability = fill_probability

    def execute(
        self,
        action: float,
        price: float,
        volatility: float,
        liquidity: float,
    ) -> dict[str, Any]:
        """Attempt to fill ``action`` shares at ``price`` (signed for direction)."""
        if np.random.random() > self.fill_probability:
            return {"filled": False, "price": None, "shares": 0}

        slippage = price * volatility * 0.10 / max(liquidity, 0.1)
        execution_price = price + slippage * np.sign(action)

        return {"filled": True, "price": execution_price, "shares": action}

    def overnight_gap(self, close: float, volatility: float) -> float:
        """Draw an overnight gap and apply it to ``close``."""
        gap = np.random.normal(0, volatility)
        return close * (1 + gap)
