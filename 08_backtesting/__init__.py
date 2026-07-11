"""
AURORA-SWING — Module 08: Backtesting & Validation Engine.

A quant system is not judged by "it made money in backtest". This module proves
the edge survives unseen data (walk-forward), randomness (Monte Carlo) and holds
up under professional risk-adjusted metrics.
"""

from .evaluation import PerformanceEvaluator
from .monte_carlo import MonteCarloSimulator
from .walk_forward import WalkForwardEngine, WalkForwardWindow

__all__ = [
    "WalkForwardWindow",
    "WalkForwardEngine",
    "MonteCarloSimulator",
    "PerformanceEvaluator",
]
