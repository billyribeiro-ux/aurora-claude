"""
AURORA-SWING

Adaptive Volatility Model
=========================

Provides adaptive volatility measurements — realized volatility, volatility
percentile (regime) and ATR-based stop distances — used for volatility
targeting throughout the risk engine.
"""

from __future__ import annotations

from typing import Any

import numpy as np

__all__ = ["VolatilityModel"]


class VolatilityModel:
    """Realized / annualized volatility and ATR stop helpers."""

    def __init__(self, annualization_factor: int = 252) -> None:
        self.annualization_factor = annualization_factor

    def realized_volatility(self, returns: Any, window: int = 20) -> Any:
        """Annualized rolling standard deviation of ``returns``."""
        vol = returns.rolling(window).std()
        return vol * np.sqrt(self.annualization_factor)

    def volatility_percentile(self, current_vol: float, historical_vol: Any) -> float:
        """Fraction of history below the current volatility (regime gauge)."""
        return (historical_vol < current_vol).mean()

    def atr_stop(self, atr: float, multiplier: float) -> float:
        """Stop distance as an ATR multiple."""
        return atr * multiplier
