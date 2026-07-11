"""
AURORA-SWING

Portfolio Accounting Engine
===========================

Tracks equity, positions, risk, realized/unrealized P&L and the trade lifecycle
consumed by the environment, RL agent and risk engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["Position", "Portfolio"]


@dataclass
class Position:
    """A single open position."""

    symbol: str
    shares: int
    entry_price: float
    stop_price: float
    target_price: float
    entry_day: int


@dataclass
class Portfolio:
    """Cash + open positions with mark-to-market equity accounting."""

    starting_capital: float
    cash: float | None = None
    positions: list[Position] = field(default_factory=list)
    realized_pnl: float = 0.0

    def __post_init__(self) -> None:
        if self.cash is None:
            self.cash = self.starting_capital

    @property
    def invested_capital(self) -> float:
        """Cost basis of all open positions."""
        return sum(abs(p.shares * p.entry_price) for p in self.positions)

    def equity(self, prices: dict[str, float]) -> float:
        """Total equity = cash + cost basis + unrealized P&L (mark-to-market)."""
        unrealized = 0.0
        for position in self.positions:
            current = prices[position.symbol]
            unrealized += (current - position.entry_price) * position.shares
        return self.cash + unrealized + self.invested_capital

    def add_position(self, position: Position) -> None:
        self.positions.append(position)

    def remove_position(self, symbol: str) -> None:
        self.positions = [p for p in self.positions if p.symbol != symbol]
