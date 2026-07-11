"""
AURORA-SWING — Module 05: Institutional Risk Engine.

The firewall that prevents the AI from blowing up. It has independent override
authority: the agent proposes, the risk engine disposes (APPROVED / MODIFIED /
DENIED) based on volatility, exposure, correlation, regime, drawdown and gap
risk.
"""

from .gap_risk import GapRiskModel
from .position_sizing import PositionSizer
from .risk_manager import RiskLimits, RiskManager
from .volatility_model import VolatilityModel

__all__ = [
    "VolatilityModel",
    "PositionSizer",
    "GapRiskModel",
    "RiskLimits",
    "RiskManager",
]
