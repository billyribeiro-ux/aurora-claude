"""
AURORA-SWING

Risk-Adjusted Swing Trading Reward
==================================

Arguably the most important RL component. Rewarding raw profit produces gambling
behaviour; this function rewards profitability *and* consistency, risk-adjusted
returns and capital preservation:

    R = P − D − V − G − T

where P = profit, D = drawdown penalty, V = volatility penalty,
G = overnight gap exposure, T = time decay.
"""

from __future__ import annotations

import numpy as np

__all__ = ["TradingReward"]


class TradingReward:
    """Compute the risk-adjusted reward for a step / trade."""

    def calculate(
        self,
        equity_change: float,
        drawdown: float,
        volatility: float,
        gap_risk: float,
        days_held: int,
    ) -> float:
        profit_component = np.log(1 + equity_change)
        drawdown_penalty = 5 * max(drawdown, 0)
        volatility_penalty = volatility * 2
        gap_penalty = gap_risk * 2
        time_penalty = days_held * 0.001

        return (
            profit_component
            - drawdown_penalty
            - volatility_penalty
            - gap_penalty
            - time_penalty
        )
