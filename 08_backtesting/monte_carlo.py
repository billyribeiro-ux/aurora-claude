"""
AURORA-SWING

Monte Carlo Robustness Testing
==============================

Determines whether results are robust or merely lucky by resampling the trade
sequence. If the edge only survives one particular ordering of trades, it is not
a real edge.
"""

from __future__ import annotations

from typing import Any

import numpy as np

__all__ = ["MonteCarloSimulator"]


class MonteCarloSimulator:
    """Resample trade returns to bound the distribution of outcomes."""

    def __init__(self, simulations: int = 1000) -> None:
        self.simulations = simulations

    def shuffle_returns(self, returns: np.ndarray) -> np.ndarray:
        """Total return over many random permutations of the trade sequence."""
        results: list[float] = []
        for _ in range(self.simulations):
            shuffled = np.random.permutation(returns)
            equity = np.cumprod(1 + shuffled)
            results.append(equity[-1] - 1)
        return np.array(results)

    def statistics(self, results: np.ndarray) -> dict[str, Any]:
        """Median and 5th/95th-percentile (worst/best) outcomes."""
        return {
            "median": np.median(results),
            "worst": np.percentile(results, 5),
            "best": np.percentile(results, 95),
        }
