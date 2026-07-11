"""
AURORA-SWING

Monte Carlo Robustness Testing
==============================

Determines whether results are robust or merely lucky. Two complementary tests:

* **Trade-order randomization** (``shuffle_returns``) permutes the trade
  sequence. Note that the *final* compounded return is mathematically
  order-invariant — ``prod(1 + r_i)`` is the same for any permutation — so the
  informative output of a shuffle is the **path-dependent** statistic:
  maximum drawdown, which very much depends on order. A strategy whose edge
  disappears once a cluster of losers lands together is fragile.

* **Bootstrap resampling** (``bootstrap_returns``) resamples trades *with
  replacement*. This varies both the final return and the drawdown, and is the
  right tool for a confidence interval on the edge itself.

Both return distributions of ``final_return`` and ``max_drawdown``.
"""

from __future__ import annotations

from typing import Any

import numpy as np

__all__ = ["MonteCarloSimulator"]


class MonteCarloSimulator:
    """Resample trade returns to bound the distribution of outcomes."""

    def __init__(self, simulations: int = 1000) -> None:
        self.simulations = simulations

    @staticmethod
    def _max_drawdown(equity: np.ndarray) -> float:
        peak = np.maximum.accumulate(equity)
        return float(np.min(equity / peak - 1.0))

    def shuffle_returns(self, returns: np.ndarray) -> dict[str, np.ndarray]:
        """Permute trade order; report final return and (order-dependent) drawdown.

        The final return distribution is degenerate by construction (order
        invariant) — inspect ``max_drawdown`` to judge path robustness.
        """
        r = np.asarray(returns, dtype=float)
        finals = np.empty(self.simulations)
        drawdowns = np.empty(self.simulations)
        for i in range(self.simulations):
            equity = np.cumprod(1 + np.random.permutation(r))
            finals[i] = equity[-1] - 1
            drawdowns[i] = self._max_drawdown(equity)
        return {"final_return": finals, "max_drawdown": drawdowns}

    def bootstrap_returns(self, returns: np.ndarray) -> dict[str, np.ndarray]:
        """Resample trades *with replacement*; final return and drawdown both vary."""
        r = np.asarray(returns, dtype=float)
        n = len(r)
        finals = np.empty(self.simulations)
        drawdowns = np.empty(self.simulations)
        for i in range(self.simulations):
            equity = np.cumprod(1 + np.random.choice(r, size=n, replace=True))
            finals[i] = equity[-1] - 1
            drawdowns[i] = self._max_drawdown(equity)
        return {"final_return": finals, "max_drawdown": drawdowns}

    def statistics(self, results: np.ndarray | dict[str, np.ndarray]) -> dict[str, Any]:
        """Median and 5th/95th-percentile (worst/best) of a result array.

        Accepts either a raw array (legacy) or the dict returned by
        ``shuffle_returns`` / ``bootstrap_returns`` (summarised per key).
        """
        if isinstance(results, dict):
            return {key: self._summary(np.asarray(arr)) for key, arr in results.items()}
        return self._summary(np.asarray(results))

    @staticmethod
    def _summary(arr: np.ndarray) -> dict[str, float]:
        return {
            "median": float(np.median(arr)),
            "worst": float(np.percentile(arr, 5)),
            "best": float(np.percentile(arr, 95)),
        }
