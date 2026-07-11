"""
AURORA-SWING — Module 04: High-Fidelity Swing Trading Environment.

The training ground for the RL agent. A realistic simulator models transaction
costs, slippage, execution uncertainty, overnight gaps and portfolio accounting
inside a Gym-compatible, multi-day holding framework. Garbage simulator →
garbage AI, so friction is modelled explicitly.
"""

from .execution_simulator import ExecutionSimulator
from .portfolio import Portfolio, Position
from .swing_environment import SwingTradingEnvironment
from .transaction_costs import TransactionCostModel

__all__ = [
    "Position",
    "Portfolio",
    "TransactionCostModel",
    "ExecutionSimulator",
    "SwingTradingEnvironment",
]
