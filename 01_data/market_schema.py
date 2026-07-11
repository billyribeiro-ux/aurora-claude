"""
AURORA-SWING

Market Data Schema Definitions
==============================

The immutable data structures that flow through the entire system. Defining them
once, here, prevents the common quant-research failure where every module expects
a slightly different format. All downstream models consume these structures.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np

__all__ = [
    "MarketBar",
    "FeatureVector",
    "MultiTimeframeState",
    "PortfolioState",
    "TradingAction",
    "TradeExperience",
]


@dataclass
class MarketBar:
    """A single OHLCV observation on one timeframe."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    timeframe: str


@dataclass
class FeatureVector:
    """An engineered market representation for one symbol at one instant."""

    timestamp: datetime
    symbol: str
    values: np.ndarray


@dataclass
class MultiTimeframeState:
    """A complete market observation combining Daily, 4H, 1H and market context."""

    symbol: str
    timestamp: datetime
    daily_features: np.ndarray
    four_hour_features: np.ndarray
    hourly_features: np.ndarray | None
    market_context: np.ndarray


@dataclass
class PortfolioState:
    """The current portfolio condition presented to the RL agent and risk engine."""

    capital: float
    cash: float
    equity: float
    position_size: float
    entry_price: float
    unrealized_pnl: float
    realized_pnl: float
    days_held: int


@dataclass
class TradingAction:
    """The RL agent's output for a single decision step."""

    #: -1 short, 0 flat, +1 long
    direction: int
    position_fraction: float
    stop_atr_multiple: float
    target_multiple: float
    trailing_strength: float


@dataclass
class TradeExperience:
    """A single transition stored for continual learning / replay."""

    state: np.ndarray
    action: TradingAction
    reward: float
    next_state: np.ndarray
    done: bool
    regime: int
    uncertainty: float
