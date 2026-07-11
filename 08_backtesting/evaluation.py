"""
AURORA-SWING

Performance Evaluation Framework
================================

Institutional performance metrics: total return, maximum drawdown, annualized
volatility and the risk-adjusted Sharpe and Sortino ratios.
"""

from __future__ import annotations

from typing import Any

import numpy as np

__all__ = ["PerformanceEvaluator"]


class PerformanceEvaluator:
    """Compute return / risk / risk-adjusted metrics from a return series."""

    def __init__(self, risk_free: float = 0.04) -> None:
        self.risk_free = risk_free

    def calculate(self, returns: np.ndarray) -> dict[str, Any]:
        equity = np.cumprod(1 + returns)
        total_return = equity[-1] - 1

        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak
        max_drawdown = drawdown.min()

        volatility = np.std(returns) * np.sqrt(252)

        sharpe = (
            (np.mean(returns) - self.risk_free / 252) / (np.std(returns) + 1e-9)
        ) * np.sqrt(252)

        downside = returns[returns < 0]
        sortino = (np.mean(returns) / (np.std(downside) + 1e-9)) * np.sqrt(252)

        return {
            "return": total_return,
            "max_drawdown": max_drawdown,
            "volatility": volatility,
            "sharpe": sharpe,
            "sortino": sortino,
        }
