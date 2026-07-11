"""
AURORA-SWING — Module 10: Production Deployment Engine.

The layer that turns AURORA-SWING from a research system into an operating
autonomous quant platform. Four responsibilities:

    1. Load trained models        (dependency-injected into AuroraLiveEngine)
    2. Process live market state  (AuroraLiveEngine.analyze_market)
    3. Generate decisions         (SignalGenerator.generate -> TradingSignal)
    4. Monitor system health      (ModelMonitor.check_health)

The live system never trades directly from the neural-network output; every
action passes the risk firewall before becoming an approved trade.
"""

from .live_engine import AuroraLiveEngine
from .monitoring import HealthThresholds, ModelMonitor
from .signal_service import SignalGenerator, TradingSignal

__all__ = [
    "AuroraLiveEngine",
    "SignalGenerator",
    "TradingSignal",
    "ModelMonitor",
    "HealthThresholds",
]
