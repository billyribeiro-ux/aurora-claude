"""
AURORA-SWING

Transaction Cost Model
======================

Models realistic trading friction so the RL agent never learns from a fantasy
of frictionless fills. Includes commissions, spread, liquidity impact and
volatility-adjusted slippage.
"""

from __future__ import annotations

__all__ = ["TransactionCostModel"]


class TransactionCostModel:
    """Estimate the round-friction cost of trading ``shares`` at ``price``."""

    def __init__(
        self,
        commission_per_share: float = 0.005,
        base_spread: float = 0.0005,
    ) -> None:
        self.commission = commission_per_share
        self.base_spread = base_spread

    def estimate_cost(
        self,
        price: float,
        shares: float,
        volatility: float,
        volume_ratio: float,
    ) -> float:
        """Total friction cost for the order.

        Parameters
        ----------
        price:
            Execution price per share.
        shares:
            Number of shares (absolute).
        volatility:
            Recent volatility (fractional) driving slippage.
        volume_ratio:
            Order size relative to available liquidity; > 1 adds impact.
        """
        spread_cost = price * self.base_spread
        volatility_slippage = price * volatility * 0.25
        liquidity_penalty = max(volume_ratio - 1, 0) * 0.001

        total_per_share = (
            spread_cost + volatility_slippage + liquidity_penalty + self.commission
        )
        return total_per_share * shares
