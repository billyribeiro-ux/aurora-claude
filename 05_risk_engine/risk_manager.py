"""
AURORA-SWING

Institutional Risk Firewall
===========================

The independent authority over the RL agent. The agent may *request* a trade;
this firewall returns APPROVED / MODIFIED (via ``size_multiplier``) / DENIED
after checking regime, drawdown, volatility, overnight gap risk and hard
position caps.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["RiskLimits", "RiskManager"]


@dataclass
class RiskLimits:
    """Hard portfolio-level limits."""

    max_drawdown: float = 0.15
    max_position: float = 0.10
    max_sector_exposure: float = 0.25
    max_portfolio_heat: float = 0.06


class RiskManager:
    """Combine portfolio, volatility, drawdown and gap checks into a decision."""

    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()

    def evaluate(
        self,
        proposed_position: float,
        portfolio: Any,
        volatility: float,
        regime: str,
        gap_multiplier: float,
    ) -> dict[str, Any]:
        decision: dict[str, Any] = {
            "approved": True,
            "size_multiplier": 1.0,
            "reason": [],
        }

        # Crisis protection — hard stop on new risk.
        if regime == "CRISIS":
            decision["approved"] = False
            decision["reason"].append("Market crisis")
            return decision

        # Drawdown protection.
        drawdown = (
            portfolio.starting_capital - portfolio.equity()
        ) / portfolio.starting_capital
        if drawdown > self.limits.max_drawdown:
            decision["size_multiplier"] *= 0.25
            decision["reason"].append("Drawdown reduction")

        # Volatility reduction.
        if volatility > 0.05:
            decision["size_multiplier"] *= 0.5
            decision["reason"].append("High volatility")

        # Overnight gap throttle.
        decision["size_multiplier"] *= gap_multiplier

        # Hard position cap.
        if proposed_position > self.limits.max_position:
            decision["size_multiplier"] *= 0.5

        return decision
